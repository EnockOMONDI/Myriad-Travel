from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.http import Http404
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserBookings, UserProfile, BucketList, Booking
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.http import JsonResponse


from adminside.models import *
from users.models import *
from .forms import UserRegisterForm
from .forms import UserBookingsForm
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
# Create your views here.

from tours_travels import mail as mail_f
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes, DjangoUnicodeDecodeError
from .utils import generate_token
from django.views import View
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .forms import UserRegisterForm

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .utils import send_booking_confirmation_email
from .forms import MICEInquiryForm, StudentTravelInquiryForm, NGOTravelInquiryForm, JobApplicationForm, NewsletterSubscriptionSimpleForm, QuoteRequestForm, TripFeedbackForm
from .models import QuoteRequest, TripFeedback
from django.contrib.auth.models import User
from blog.models import Post, Category
from adminside.models import Destination, Package, Accommodation
from django.utils.text import slugify
from django.utils.html import strip_tags
from types import SimpleNamespace
from html.parser import HTMLParser


class _ListItemParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self._in_li = False
        self._current = []

    def handle_starttag(self, tag, attrs):
        if tag == 'li':
            self._in_li = True
            self._current = []

    def handle_endtag(self, tag):
        if tag == 'li' and self._in_li:
            item = ' '.join(''.join(self._current).split())
            if item:
                self.items.append(item)
            self._in_li = False

    def handle_data(self, data):
        if self._in_li:
            self._current.append(data)


CHALBI_SPECIAL_OFFER = {
    'label': 'Current Featured Activation',
    'date': '10-14 December 2026',
    'departure': 'Nairobi departure at 3:30 AM on 10 December 2026',
    'return': 'Nairobi return around 4:00-5:00 PM on 14 December 2026',
    'single_occupancy_price': 66000,
    'notes': [
        'Expect long stretches of rough, dusty and corrugated roads across the northern frontier.',
        'Network coverage may be limited in some sections; download key documents and maps before departure.',
        'The early Nairobi departure and morning starts are important because delays can affect later activities.',
        'December days can be hot, while early mornings and evenings may feel cooler.',
        'Accommodation may be split by capacity on some nights while meals and activities remain coordinated.',
    ],
    'packing_list': [
        'Refillable water bottle, sunscreen, hat or cap, sunglasses and mosquito repellent.',
        'Dust scarf or shuka, light comfortable clothing, warm jacket and comfortable shoes.',
        'Swimwear and towel for Lake Turkana, plus a power bank and charging cables.',
        'Personal medication, toiletries, wet wipes, sanitiser, tissues and identification documents.',
        'Small cash in Kenyan shillings for personal purchases and incidentals.',
    ],
    'before_faqs': [
        {
            'question': 'Is this adventure right for me?',
            'answer': 'This trip is best for travellers who enjoy road adventure, remote landscapes, early starts, dusty terrain and flexible timing. It is scenic, social and guided, but it is not a soft city break.',
        },
        {
            'question': 'What should I pack?',
            'answer': 'Carry sun protection, a dust scarf or shuka, comfortable shoes, warm layers, swimwear, a towel, a power bank, personal medication and identification documents.',
        },
        {
            'question': 'Can children join, and how does room sharing work?',
            'answer': 'Children can be considered with the Myriad team confirming rooming, age suitability and final pricing before booking. The current child rate is stored separately from the adult sharing rate.',
        },
        {
            'question': 'What happens after I send my request?',
            'answer': 'Myriad Travel will confirm availability, rooming preference, inclusions, final payment steps and any operational updates before your booking is locked in.',
        },
    ],
}


CHALBI_DAY_META = {
    1: {
        'date': 'Thu, 10 Dec',
        'theme': 'Into the North',
        'title': 'Nairobi to Marsabit',
        'summary': 'Nanyuki - Samburu - Mount Ololokwe',
        'overnight': 'Marsabit',
    },
    2: {
        'date': 'Fri, 11 Dec',
        'theme': 'Desert Days',
        'title': 'Marsabit to Chalbi & North Horr',
        'summary': 'Salt flats - Desert walks - Sunset dunes',
        'overnight': 'North Horr',
    },
    3: {
        'date': 'Sat, 12 Dec',
        'theme': 'By the Jade Sea',
        'title': 'North Horr to Lake Turkana',
        'summary': 'Loiyangalani - Boat experience - El Molo',
        'overnight': 'Lake Turkana / Loiyangalani',
    },
    4: {
        'date': 'Sun, 13 Dec',
        'theme': 'The Scenic Route',
        'title': 'Lake Turkana to Isiolo',
        'summary': 'Wind Power route - Ngurunit - Archers Post',
        'overnight': 'Isiolo',
    },
    5: {
        'date': 'Mon, 14 Dec',
        'theme': 'Home, With Stories',
        'title': 'Isiolo to Nairobi',
        'summary': 'A slow breakfast - The journey home',
        'overnight': '',
    },
}


def _image_url(image_field, fallback):
    if image_field and hasattr(image_field, 'cdn_url'):
        return image_field.cdn_url
    if image_field and hasattr(image_field, 'url'):
        try:
            return image_field.url
        except (ValueError, AttributeError):
            pass
    return fallback


def _uploadcare_preview_url(image_field, fallback, width=1600, height=900):
    uuid = getattr(image_field, 'uuid', None)
    if uuid:
        return f'https://ucarecdn.com/{uuid}/-/preview/{width}x{height}/'
    return _image_url(image_field, fallback)


def _rich_text_items(value):
    if not value:
        return []
    parser = _ListItemParser()
    parser.feed(str(value))
    if parser.items:
        return parser.items

    plain = strip_tags(str(value))
    return [line.strip(' -*\t') for line in plain.splitlines() if line.strip(' -*\t')]


def _package_presenter(package):
    category = package.category.name if package.category else 'Safari & Holiday'
    destination = package.main_destination.get_full_name() if package.main_destination else 'Kenya'
    price_kes = int(package.adult_price or 0)
    highlights = [line.strip() for line in (package.highlights or '').splitlines() if line.strip()]
    region_label = package.get_region_display() if hasattr(package, 'get_region_display') else category
    lipa_months = package.lipa_pole_pole_months or 4
    special_offer = CHALBI_SPECIAL_OFFER if package.slug == 'twende-chalbi-4-nights-5-days' else None
    itinerary_days = _itinerary_presenter(package)
    accommodations = list(package.available_accommodations.all())
    travel_modes = list(package.available_travel_modes.all())
    accommodation_names = [item.name for item in accommodations[:3]]
    transport_names = [item.get_transport_type_display() for item in travel_modes[:3]]
    plain_description = ' '.join(strip_tags(str(package.description or '')).split())
    intro = package.subtitle or package.meta_description or plain_description
    if len(intro) > 260:
        intro = f'{intro[:257].rstrip()}...'
    best_for = {
        'kenya-safari': 'Safari, wildlife and scenic road adventure',
        'kenya-coast': 'Beach holidays, coastal escapes and relaxed stays',
        'international': 'International holidays and curated city escapes',
        'day-trips': 'Short breaks, weekend escapes and group outings',
    }.get(package.region, 'Curated Myriad Travel experience')
    route_summary = ' -> '.join(day['title'] for day in itinerary_days[:4]) if itinerary_days else destination
    if itinerary_days and len(itinerary_days) > 4:
        route_summary = f'{route_summary} -> ...'
    return {
        'id': package.id,
        'slug': package.slug,
        'title': package.name,
        'subtitle': intro,
        'description': package.description,
        'category': category,
        'region_label': region_label,
        'region': package.region or slugify(category) or 'kenya-safari',
        'destination': destination,
        'featured_image': _image_url(package.featured_image, '/static/images/placeholders/myriad-package-placeholder.png'),
        'hero_image': _uploadcare_preview_url(package.featured_image, '/static/images/placeholders/myriad-package-placeholder.png'),
        'duration': f'{package.duration_days} Days / {package.duration_nights} Nights',
        'rating': package.rating,
        'reviews_count': package.total_reviews,
        'price_kes': price_kes,
        'child_price_kes': int(package.child_price or 0),
        'single_price_kes': int(special_offer['single_occupancy_price']) if special_offer else 0,
        'price_usd': round(price_kes / 130) if price_kes else 0,
        'lipa_pole_pole': package.lipa_pole_pole,
        'lipa_pole_pole_months': lipa_months,
        'price_kes_monthly': round(price_kes / lipa_months) if price_kes and lipa_months else 0,
        'price_usd_monthly': round((price_kes / 130) / lipa_months) if price_kes and lipa_months else 0,
        'highlights': highlights,
        'inclusions': _rich_text_items(package.inclusions),
        'exclusions': _rich_text_items(package.exclusions),
        'itinerary': itinerary_days,
        'best_for': best_for,
        'route_summary': route_summary,
        'accommodations': accommodation_names,
        'transport_modes': transport_names,
        'has_image': bool(package.featured_image),
        'special_offer': special_offer,
        'model': package,
    }


def _itinerary_presenter(package):
    days = []
    try:
        itinerary = package.itinerary
    except Exception:
        itinerary = None
    if itinerary:
        for day in itinerary.days.all().order_by('day_number'):
            meals = ', '.join(label for ok, label in [
                (day.breakfast, 'Breakfast'),
                (day.lunch, 'Lunch'),
                (day.dinner, 'Dinner'),
            ] if ok)
            days.append({
                'day': day.day_number,
                'title': CHALBI_DAY_META.get(day.day_number, {}).get('title', day.title) if package.slug == 'twende-chalbi-4-nights-5-days' else day.title,
                'description': day.description,
                'meals': meals,
                'stay': day.accommodation.name if day.accommodation else '',
                'date': CHALBI_DAY_META.get(day.day_number, {}).get('date', ''),
                'theme': CHALBI_DAY_META.get(day.day_number, {}).get('theme', ''),
                'summary': CHALBI_DAY_META.get(day.day_number, {}).get('summary', ''),
                'overnight': CHALBI_DAY_META.get(day.day_number, {}).get('overnight', ''),
            })
    return days


def _destination_presenter(destination):
    country = destination.country.name if destination.country else 'Kenya'
    return {
        'id': destination.id,
        'name': destination.name,
        'slug': destination.slug,
        'country': country,
        'description': destination.meta_description or destination.description,
        'image': _image_url(destination.image, 'https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?q=80&w=1200&auto=format&fit=crop'),
        'badge': 'Featured' if destination.is_featured else destination.get_destination_type_display(),
        'popular_for': ['Safari', 'Nature', 'Tailored Trips'],
        'model': destination,
    }


def _public_page_context(package_limit=None):
    packages_qs = Package.objects.select_related('main_destination', 'category').prefetch_related(
        'available_accommodations',
        'available_travel_modes',
        'itinerary__days',
    ).filter(status=Package.PUBLISHED).order_by('home_rank', '-is_featured', '-published_at', '-created_at')
    if package_limit:
        packages_qs = packages_qs[:package_limit]

    destinations_qs = Destination.objects.filter(is_active=True).order_by('-is_featured', 'display_order', 'name')[:12]
    trip_feedbacks = TripFeedback.objects.filter(
        is_visible_on_site=True,
        permission_to_publish=True,
        status__in=[TripFeedback.SUBMITTED, TripFeedback.REVIEWED],
    ).order_by('-is_featured', '-submitted_at', '-created_at')[:6]
    return {
        'packages': [_package_presenter(package) for package in packages_qs],
        'featured_destinations': [_destination_presenter(dest) for dest in destinations_qs],
        'all_destinations': destinations_qs,
        'trip_feedbacks': trip_feedbacks,
    }






def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request=request)

        if form.is_valid():
            from .antispam import check_form_submission
            if not check_form_submission(request, form.cleaned_data.get('email', '')):
                form.add_error(None, 'We have received several requests recently. Please wait a little before trying again.')
                return render(request, 'users/register.html', {'form': form})
            user = form.save(commit=False)  # Save the user object in memory
            user.is_active = False

            # Save the user object to the database only when the form is valid
            user.save()

            current_site = get_current_site(request)
            uid64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)
            activation_link = f'http://{current_site}/activate/{uid64}/{token}'

            mail_f.verification_mail(activation_link, user)

            # Store username and email in session
            request.session['username'] = form.cleaned_data['username']
            request.session['email'] = form.cleaned_data['email']

            # Redirect to the success message page
            return redirect('users:success')

    else:
        form = UserRegisterForm(request=request)

    return render(request, 'users/register.html', {'form': form})




def success(request):
    username = request.session.pop('username', None)
    email = request.session.pop('email', None)

    if username and email:
        success_message = f"Jambo! <b>{username}</b>, Your registration was successful! We've sent an email to <b>{email}</b>. Kindly click the received link to confirm and complete the registration. Remember to check your spam folder."
        messages.success(request, success_message)
    else:
        messages.error(request, 'Oops! Something is not right. Please start over.')

    return render(request, 'users/success.html')


def aboutus(request):

    return render(request, 'users/aboutus.html')


def services(request):
    """
    Render the services page showcasing all Mbugani Luxe Adventures services.
    """
    return render(request, 'users/pages/services.html', _public_page_context(package_limit=6))


def corporate(request):

    return render(request, 'users/corporate.html')

# users/views.py


def _service_inquiry(request, form_class, template_name, route_name, title):
    """Save once, notify over HTTPS, and redirect even if notification fails."""
    from .inquiry_email import send_service_inquiry_emails

    form = form_class(request.POST if request.method == 'POST' else None, request=request)
    if request.method == 'POST' and form.is_valid():
        from .antispam import check_form_submission
        if not check_form_submission(request, form.cleaned_data.get('email', '')):
            form.add_error(None, 'We have received several requests recently. Please wait a little before submitting again.')
            return render(request, template_name, {'form': form})
        inquiry = form.save()
        sent = send_service_inquiry_emails(inquiry, form, title)
        if sent:
            messages.success(request, 'Thank you! Your inquiry has been submitted successfully. We will contact you soon.')
        else:
            messages.warning(request, 'Your inquiry has been saved, but the email notification could not be sent. Please do not resubmit. You can contact us directly for assistance.')
        return redirect(route_name)
    return render(request, template_name, {'form': form})


def micepage(request):
    return _service_inquiry(request, MICEInquiryForm, 'users/mice.html', 'users:micepage', 'MICE')


def student_travel(request):
    return _service_inquiry(request, StudentTravelInquiryForm, 'users/student_travel.html', 'users:student-travel', 'Student Travel')


def ngo_travel(request):
    return _service_inquiry(request, NGOTravelInquiryForm, 'users/ngo_travel.html', 'users:ngo-travel', 'NGO Travel')


def holidays(request):

    return render(request, 'users/pages/packages.html', _public_page_context())

def contactus(request):
    if request.method == 'POST':
        data = request.POST.copy()
        data['phone_number'] = data.get('phone', '')
        data['destination'] = data.get('subject') or 'General travel enquiry'
        data['preferred_travel_dates'] = 'To be discussed'
        data['number_of_travelers'] = '1'
        data['special_requests'] = data.get('message', '')
        form = QuoteRequestForm(data, request=request)
        if form.is_valid():
            from .antispam import check_form_submission
            if not check_form_submission(request, form.cleaned_data.get('email', '')):
                form.add_error(None, 'We have received several requests recently. Please wait a little before submitting again.')
            else:
                quote_request = form.save()
                from users.tasks import send_quote_request_emails
                result = send_quote_request_emails(quote_request.id)
                if result.get('success'):
                    messages.success(request, 'Thank you. Your request has been received. We will respond within 2 hours where possible and within 24 hours at the latest.')
                else:
                    messages.warning(request, 'Your request was saved, but the email notification could not be completed. Please do not resubmit.')
                return redirect('users:contact')
        messages.error(request, 'Please complete the security check and correct any highlighted fields.')
    else:
        form = None
    return render(request, 'users/pages/contact.html', {'contact_form': form})


def packages(request):
    return render(request, 'users/pages/packages.html', _public_page_context())


SIGNATURE_CATEGORY_SLUGS = [
    'cruises',
    'wellness-retreats',
    'shopping-tours',
    'religious-pilgrimages',
    'honeymoon-packages',
]

TOURS_SAFARI_CATEGORY_SLUGS = [
    'adventure-safaris',
    'bird-watching-safaris',
    'budget-safaris',
    'camping-safaris',
    'cultural-safaris',
    'family-safaris',
    'flying-safaris',
    'honeymoon-safaris',
    'luxury-safaris',
    'mountain-climbing-safaris',
    'photography-safaris',
    'bush-and-beach-safaris',
    'northern-kenya-adventure',
    'big-five-migration-safari',
    'wildlife-photography',
    'hiking-day-adventure',
    'beach-holiday-water-sports',
]


def _packages_for_collection():
    return Package.objects.select_related('main_destination', 'category').prefetch_related(
        'available_accommodations',
        'available_travel_modes',
        'itinerary__days',
    ).filter(status=Package.PUBLISHED).order_by('home_rank', '-is_featured', '-published_at', '-created_at')


def _collection_context(title, eyebrow, description, packages_qs, destination_qs=None, groups=None, active_filter='all'):
    context = _public_page_context(package_limit=4)
    packages = list(packages_qs)
    filters = []
    seen_filters = set()
    for package in packages:
        if package.category:
            slug = slugify(package.category.name)
            if slug not in seen_filters:
                seen_filters.add(slug)
                filters.append({
                    'label': package.category.name,
                    'slug': slug,
                })
    context.update({
        'collection_title': title,
        'collection_eyebrow': eyebrow,
        'collection_description': description,
        'collection_packages': [_package_presenter(package) for package in packages],
        'collection_destinations': destination_qs or [],
        'collection_filters': filters,
        'collection_active_filter': active_filter or 'all',
        'collection_groups': groups or [],
    })
    return context


def explore_kenya(request):
    packages_qs = _packages_for_collection().filter(region__in=['kenya-safari', 'kenya-coast', 'day-trips'])
    destinations_qs = Destination.objects.filter(
        is_active=True,
        packages__status=Package.PUBLISHED,
        packages__region__in=['kenya-safari', 'kenya-coast', 'day-trips'],
    ).distinct().order_by('-is_featured', 'display_order', 'name')[:12]
    context = _collection_context(
        'Explore Kenya',
        'Kenya holidays, safaris and coast escapes',
        'Find the Kenya experiences Myriad Travel can shape around your dates, from desert campaigns and wildlife safaris to coast stays and weekend escapes.',
        packages_qs,
        destinations_qs,
    )
    return render(request, 'users/pages/collection.html', context)


def explore_the_world(request):
    packages_qs = _packages_for_collection().filter(region='international').exclude(category__slug__in=SIGNATURE_CATEGORY_SLUGS)
    destinations_qs = Destination.objects.filter(
        is_active=True,
        packages__status=Package.PUBLISHED,
        packages__region='international',
    ).distinct().order_by('-is_featured', 'display_order', 'name')[:12]
    context = _collection_context(
        'Explore World Destinations',
        'International holidays from Myriad Travel',
        'Browse global holidays, city breaks and island escapes with planning support from enquiry to confirmed itinerary.',
        packages_qs,
        destinations_qs,
    )
    return render(request, 'users/pages/collection.html', context)


def tours_safaris(request):
    packages_qs = _packages_for_collection().filter(
        Q(region__in=['kenya-safari', 'kenya-coast', 'day-trips']) |
        Q(category__slug__in=TOURS_SAFARI_CATEGORY_SLUGS)
    ).exclude(category__slug__in=SIGNATURE_CATEGORY_SLUGS)
    selected_category = request.GET.get('category', '').strip()
    selected_filter = slugify(selected_category) if selected_category else 'all'
    context = _collection_context(
        'Tours & Safaris',
        'Safari, coast and adventure planning',
        'Safari, coast, mountain, culture, photography and adventure trips gathered into one clear planning space. Start with a style, then open the package that fits your dates and group.',
        packages_qs,
        active_filter=selected_filter,
    )
    return render(request, 'users/pages/collection.html', context)


def signature_experiences(request):
    groups = []
    packages_qs = _packages_for_collection().filter(category__slug__in=SIGNATURE_CATEGORY_SLUGS)
    for category in PackageCategory.objects.filter(slug__in=SIGNATURE_CATEGORY_SLUGS, is_active=True).order_by('display_order', 'name'):
        group_packages = [pkg for pkg in packages_qs if pkg.category_id == category.id]
        if group_packages:
            groups.append({
                'title': category.name,
                'description': category.description,
                'packages': [_package_presenter(package) for package in group_packages],
            })
    context = _collection_context(
        'Signature Experiences',
        'Curated journeys for a specific reason to travel',
        'Cruises, wellness retreats, shopping tours, pilgrimages and honeymoon escapes prepared as ready-to-enquire Myriad Travel experiences.',
        packages_qs,
        groups=groups,
    )
    return render(request, 'users/pages/signature_experiences.html', context)


def destinations(request):
    return render(request, 'users/pages/destinations.html', _public_page_context())


def destination_detail(request, slug):
    destination = get_object_or_404(Destination, slug=slug, is_active=True)
    packages_qs = _packages_for_collection().filter(main_destination=destination)
    context = _collection_context(
        destination.name,
        'Destination guide',
        destination.meta_description or strip_tags(str(destination.description or '')),
        packages_qs,
    )
    context['destination'] = _destination_presenter(destination)
    return render(request, 'users/pages/destination_detail.html', context)


def package_detail(request, slug):
    package = get_object_or_404(
        Package.objects.select_related('main_destination', 'category').prefetch_related('itinerary__days'),
        slug=slug,
        status=Package.PUBLISHED,
    )
    context = _public_page_context(package_limit=6)
    context['pkg'] = _package_presenter(package)
    template_name = (
        'users/pages/package_detail_chalbi.html'
        if package.slug == 'twende-chalbi-4-nights-5-days'
        else 'users/pages/package_detail.html'
    )
    return render(request, template_name, context)


def package_gallery(request, slug):
    package = get_object_or_404(
        Package.objects.select_related('main_destination', 'category').prefetch_related('gallery_images'),
        slug=slug,
        status=Package.PUBLISHED,
    )
    context = _public_page_context(package_limit=4)
    context['pkg'] = _package_presenter(package)
    context['gallery_images'] = package.gallery_images.filter(is_visible=True)
    return render(request, 'users/pages/package_gallery.html', context)


def send_job_application_emails(job_application):
    """
    Send job application emails synchronously using Mailtrap HTTP API
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        from users.tasks import send_job_application_emails as send_emails_task

        # Send emails synchronously
        result = send_emails_task(job_application.id)

        if result.get('success'):
            logger.info(f"Job application emails sent successfully: application_id={job_application.id}")
            return True
        else:
            logger.error(f"Failed to send job application emails for {job_application.id}")
            return False

    except Exception as e:
        logger.error(f"Failed to send job application emails for {job_application.id}: {e}")
        return False


def send_newsletter_subscription_emails(subscription):
    """
    Send newsletter subscription emails synchronously using Mailtrap HTTP API
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        from users.tasks import send_newsletter_subscription_emails as send_emails_task

        # Send emails synchronously
        result = send_emails_task(subscription.id)

        if result.get('success'):
            logger.info(f"Newsletter subscription emails sent successfully: subscription_id={subscription.id}")
            return True
        else:
            logger.error(f"Failed to send newsletter subscription emails for {subscription.id}")
            return False

    except Exception as e:
        logger.error(f"Failed to send newsletter subscription emails for {subscription.id}: {e}")
        return False


def careers(request):
    """
    Careers page with job application form and dynamic job listings
    """
    from .models import JobListing

    # Get job listings
    job_listings = JobListing.objects.filter(is_active=True).order_by('-featured', '-posted_date')

    # Filter by job type if specified
    job_type_filter = request.GET.get('job_type')
    if job_type_filter:
        job_listings = job_listings.filter(job_type=job_type_filter)

    # Filter by application status if specified
    status_filter = request.GET.get('status')
    if status_filter:
        job_listings = job_listings.filter(application_status=status_filter)

    # Handle job application form submission
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES, request=request)
        if form.is_valid():
            from .antispam import check_form_submission
            if not check_form_submission(request, form.cleaned_data.get('email', '')):
                form.add_error(None, 'We have received several requests recently. Please wait a little before submitting again.')
                return render(request, 'users/careers.html', {'form': form, 'job_listings': job_listings})
            job_application = form.save()

            # Send email notifications
            try:
                send_job_application_emails(job_application)
                messages.success(request, 'Your job application has been submitted successfully! We will review your application and get back to you soon.')
            except Exception as e:
                messages.warning(request, 'Your application was submitted, but there was an issue sending email notifications. We will still review your application.')
                print(f"Email error: {e}")

            # Redirect to prevent resubmission
            return redirect('users:careers')
    else:
        form = JobApplicationForm()

        # Pre-populate form if job_id is provided
        job_id = request.GET.get('job_id')
        if job_id:
            try:
                job_listing = JobListing.objects.get(id=job_id, is_active=True)
                # Map job listing title to form choices
                position_mapping = {
                    'accountant': 'accountant',
                    'travel consultant': 'travel_consultant',
                    'graphic designer': 'graphic_designer',
                    'marketing specialist': 'marketing_specialist',
                    'customer service representative': 'customer_service',
                    'tour guide': 'tour_guide',
                    'operations manager': 'operations_manager',
                }

                # Try to find matching position
                job_title_lower = job_listing.title.lower()
                for key, value in position_mapping.items():
                    if key in job_title_lower:
                        form.initial['position_applied_for'] = value
                        break

            except JobListing.DoesNotExist:
                pass

    # Get filter choices for the template
    job_type_choices = JobListing.JOB_TYPE_CHOICES
    status_choices = JobListing.APPLICATION_STATUS_CHOICES

    context = {
        'form': form,
        'job_listings': job_listings,
        'job_type_choices': job_type_choices,
        'status_choices': status_choices,
        'current_job_type': job_type_filter,
        'current_status': status_filter,
    }

    return render(request, 'users/careers.html', context)


def job_detail(request, slug):
    """
    Individual job detail page with access control for closed jobs
    """
    from .models import JobListing
    from django.shortcuts import get_object_or_404

    job = get_object_or_404(JobListing, slug=slug, is_active=True)

    # Check if job applications are closed
    if job.application_status == 'closed':
        # Get other open jobs to show as alternatives
        open_jobs = JobListing.objects.filter(
            application_status='open',
            is_active=True
        ).exclude(id=job.id)[:3]

        # Render a special template for closed jobs
        context = {
            'job': job,
            'is_closed': True,
            'open_jobs': open_jobs,
        }
        return render(request, 'users/job_detail_closed.html', context)

    # Get related jobs (same type, excluding current job)
    related_jobs = JobListing.objects.filter(
        job_type=job.job_type,
        is_active=True
    ).exclude(id=job.id)[:3]

    context = {
        'job': job,
        'related_jobs': related_jobs,
        'is_closed': False,
    }

    return render(request, 'users/job_detail.html', context)


def newsletter_subscribe(request):
    """
    Handle newsletter subscription from footer form
    """
    from .models import NewsletterSubscription
    from django.http import JsonResponse

    if request.method == 'POST':
        form = NewsletterSubscriptionSimpleForm(request.POST, request=request)
        if form.is_valid():
            email = form.cleaned_data['email']
            from .antispam import check_form_submission
            if not check_form_submission(request, email):
                error_message = 'Please wait a little before trying to subscribe again.'
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': error_message}, status=429)
                messages.warning(request, error_message)
                return redirect(request.META.get('HTTP_REFERER') or 'users:users-home')

            # Create subscription with default preferences
            subscription = NewsletterSubscription.objects.create(
                email=email,
                travel_tips=True,
                special_offers=True,
                destination_updates=True
            )

            # Send email notifications
            try:
                send_newsletter_subscription_emails(subscription)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Thank you for subscribing! Please check your email to confirm your subscription.'
                    })
                else:
                    messages.success(request, 'Thank you for subscribing! Please check your email to confirm your subscription.')
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'You have been subscribed, but there was an issue sending the confirmation email.'
                    })
                else:
                    messages.warning(request, 'You have been subscribed, but there was an issue sending the confirmation email.')
                print(f"Newsletter email error: {e}")
        else:
            # Form has errors
            error_message = list(form.errors.values())[0][0] if form.errors else 'Please enter a valid email address.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                })
            else:
                messages.error(request, error_message)

    # Redirect back to the referring page or homepage
    return redirect(request.META.get('HTTP_REFERER', 'users:home'))


def home(request):
    """
    Fully optimized homepage view with efficient database queries, caching, and featured accommodations
    """
    from django.core.cache import cache
    from adminside.models import Accommodation, HeroSlider
    import logging

    logger = logging.getLogger(__name__)
    logger.debug("Starting home view")

    try:
        # Get featured destinations with optimized query (limit to 8 for performance)
        featured_destinations = Destination.objects.filter(
            is_featured=True,
            is_active=True
        ).select_related().order_by('display_order', 'name')[:8]

        # Get featured accommodations with optimized query (limit to 8 for performance)
        featured_accommodations = Accommodation.objects.select_related('destination').filter(
            is_featured=True,
            is_active=True
        ).order_by('-rating', 'name')[:8]

        # Get all active destinations for navigation (limited for performance)
        all_destinations = Destination.objects.filter(
            is_active=True
        ).order_by('name')[:50]  # Limit to 50 most relevant destinations

        # Get published packages with highly optimized queries (limit to 12 for homepage)
        packages_queryset = Package.objects.select_related('main_destination', 'category').prefetch_related(
            'available_accommodations',
            'available_travel_modes'
        ).filter(status=Package.PUBLISHED).order_by('home_rank', '-is_featured', '-published_at', '-created_at')[:4]

        # Process package data efficiently with minimal loops
        package_data = []
        for package in packages_queryset:
            try:
                # Calculate nights
                nights = max(package.duration_days - 1, 0)

                # Get first accommodation price (already prefetched)
                accommodations = list(package.available_accommodations.all())
                accommodation_price = accommodations[0].price_per_room_per_night if accommodations else 0

                # Calculate total price
                total_price = package.adult_price + accommodation_price

                # Get travel mode (already prefetched)
                travel_modes = list(package.available_travel_modes.all())
                if travel_modes:
                    transport_type = travel_modes[0].transport_type
                    travel_type = {
                        "train": "Train",
                        "flight": "Flight",
                        "bus": "Bus"
                    }.get(transport_type, "Bus")
                else:
                    travel_type = "N/A"

                package_data.append({
                    'package': package,
                    'nights': nights,
                    'price': total_price,
                    'travel': travel_type
                })
            except Exception as e:
                continue

        # Get active hero slider images
        hero_slides = HeroSlider.get_active_slides()

        # Create optimized context
        context = {
            'featured_destinations': featured_destinations,
            'featured_accommodations': featured_accommodations,
            'all_destinations': all_destinations,
            'package_data': package_data,
            'packages': package_data,  # For backward compatibility with template
            'dests1': all_destinations,  # For backward compatibility
            'package1': packages_queryset,  # For backward compatibility
            'hero_slides': hero_slides,  # Dynamic hero slider data
        }

        context.update(_public_page_context(package_limit=4))
        return render(request, 'users/pages/home.html', context)


    except Exception as e:
        logger.error(f"Error in home view main try block: {e}")
        # Fallback to basic context to prevent complete failure
        try:
            basic_context = {
                'featured_destinations': [],
                'featured_accommodations': [],
                'all_destinations': [],
                'package_data': [],
                'packages': [],
                'dests1': [],
                'package1': [],
                'hero_slides': [],  # Empty hero slides for fallback
            }
            logger.debug("Using basic context fallback")
            basic_context.update(_public_page_context(package_limit=4))
            return render(request, 'users/pages/home.html', basic_context)
        except Exception as e2:
            logger.error(f"Error in home view fallback: {e2}")
            from django.http import HttpResponse
            return HttpResponse(f"Homepage temporarily unavailable. Error: {e2}", status=503)






def destination(request,id):
	id=id
	dest=Destination.objects.get(id=id)
	packs=Package.objects.filter(main_destination=dest, status=Package.PUBLISHED)
	nights=[]
	price=[]
	travel=[]

	for i in packs:
		nights.append(i.duration_days-1)
		first_accommodation = i.available_accommodations.first()
		accommodation_price = first_accommodation.price_per_room_per_night if first_accommodation else 0
		price.append(i.adult_price + accommodation_price)
		first_travel = i.available_travel_modes.first()
		if first_travel:
			if first_travel.transport_type == "train":
				travel.append("Train")
			elif first_travel.transport_type == "flight":
				travel.append("Flight")
			else:
				travel.append("Bus")
		else:
			travel.append("N/A")


	packages=zip(packs,nights,price,travel)




	context={'dest':dest,'packages':packages}

	context.update(_public_page_context())
	context['dest'] = _destination_presenter(dest)
	return render(request,'users/pages/destinations.html',context)



def search(request):
	try:
		name=request.POST.get('search','')
		name=name.lstrip()
		name=name.rstrip()
		dest=Destination.objects.filter(name__icontains=name) | Destination.objects.filter(description__icontains=name)
		print(dest[0].id)
		return redirect('users-destination', id=dest[0].id)
	except:
		messages.error(request, 'No results found for your search request')
		return HttpResponseRedirect(request.META.get('HTTP_REFERER'))









@login_required
def bookings(request, package_id):
    package = get_object_or_404(Package, id=package_id)
    form = UserBookingsForm(request.POST or None)
    context = {'form': form, 'package': package}

    if request.method == 'POST':
        if form.is_valid():
            print("Form is valid!")  # Debug print
            try:
                # Create the booking
                booking = UserBookings.objects.create(
                    user=request.user,
                    package=package,
                    full_name=form.cleaned_data['full_name'],
                    phone_number=form.cleaned_data['phone_number'],
                    number_of_adults=form.cleaned_data['number_of_adults'],
                    number_of_children=form.cleaned_data.get('number_of_children', 0),
                    number_of_rooms=form.cleaned_data['number_of_rooms'],
                    include_travelling=form.cleaned_data['include_travelling'],
                )

                # Send email notification
                send_booking_email(booking)

                return redirect('users:users-booking-success', booking_id=booking.id)

            except Exception as e:
                print(f"Booking creation error: {e}")
                messages.error(request, f'Error creating booking: {e}')
        else:
            print("Form is NOT valid!")
            print(form.errors)
            messages.error(request, 'Please correct the form errors.')

    return render(request, 'users/UserBookingsForm.html', context)


def send_booking_email(booking):
    """Send an admin notification about the legacy booking form."""
    try:
        from users.tasks import send_email_via_mailtrap

        message = f"""
        <p><strong>New Booking Alert</strong></p>
        <p><strong>Customer Name:</strong> {booking.full_name}</p>
        <p><strong>Phone Number:</strong> {booking.phone_number}</p>
        <p><strong>Package:</strong> {booking.package.name}</p>
        <p><strong>Adults:</strong> {booking.number_of_adults}</p>
        <p><strong>Children:</strong> {booking.number_of_children}</p>
        <p><strong>Rooms:</strong> {booking.number_of_rooms}</p>
        <p><strong>Include Travelling:</strong> {'Yes' if booking.include_travelling else 'No'}</p>
        """

        return send_email_via_mailtrap(
            subject=f"New Booking: {booking.full_name} for {booking.package.name}",
            html_message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[getattr(settings, 'ADMIN_EMAIL', 'info@myriad-travel.com')],
        )

    except Exception as e:
        print(f"Error sending booking email: {e}")
        return False

def booking_success(request, booking_id):
    booking = get_object_or_404(UserBookings, id=booking_id)
    return render(request, 'users/booking_success.html', {'booking': booking})






class ActivateAccountView(View):
	def get(self,request,uid64,token):
		try:
			uid = urlsafe_base64_decode(uid64).decode('utf-8')
			user=User.objects.get(pk=uid)
			print(uid)
		except Exception as identifire :
			user=None

		if user is not None and generate_token.check_token(user,token):
			user.is_active=True
			user.save()
			messages.success(request, 'account activated successfully')

			return redirect('login')
		return HttpResponse('THIS VERIFICATION CODE HAS ALREADY BEEN USED USE ANOTHER EMAIL TO CREATE AN ACCOUNT OR LOG IN WITH YOUR DETAILS')


def documentation(request):
    """
    Documentation page for Mbugani Luxe Adventures Django project
    """
    # Get project statistics for the documentation
    stats = {
        'total_destinations': Destination.objects.count(),
        'total_packages': Package.objects.count(),
        'total_accommodations': Accommodation.objects.count(),
        'total_blog_posts': Post.objects.count(),
        'total_categories': Category.objects.count(),
        'total_users': User.objects.count(),
        'published_posts': Post.objects.filter(status='published').count(),
        'featured_packages': Package.objects.filter(is_featured=True).count(),
        'active_destinations': Destination.objects.filter(is_active=True).count(),
    }

    # Get recent activity for dashboard
    recent_posts = Post.objects.filter(status='published').order_by('-date')[:5]
    recent_packages = Package.objects.filter(status='published').order_by('-created_at')[:5]

    context = {
        'stats': stats,
        'recent_posts': recent_posts,
        'recent_packages': recent_packages,
        'page_title': 'Project Documentation',
        'page_description': 'Comprehensive documentation for the Mbugani Luxe Adventures Django project including architecture, user guides, and technical specifications.',
    }

    return render(request, 'users/documentation.html', context)


@login_required
def user_profile(request):
    """
    User profile dashboard with booking history and account management
    """
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    # Get user's bookings
    bookings = Booking.objects.filter(user=user).order_by('-created_at')

    # Get bucket list items
    bucket_list = BucketList.objects.filter(user=user).order_by('-created_at')

    # Calculate statistics
    total_bookings = bookings.count()
    total_spent = sum(booking.total_amount for booking in bookings if booking.total_amount)
    upcoming_bookings = bookings.filter(status__in=['pending', 'confirmed']).count()

    context = {
        'user': user,
        'profile': profile,
        'bookings': bookings[:10],  # Show latest 10 bookings
        'bucket_list': bucket_list[:5],  # Show latest 5 bucket list items
        'total_bookings': total_bookings,
        'total_spent': total_spent,
        'upcoming_bookings': upcoming_bookings,
        'page_title': 'My Profile',
    }

    return render(request, 'users/user_profile.html', context)


@login_required
def edit_profile(request):
    """
    Edit user profile information
    """
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # Update user basic info
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()

        # Update profile info
        profile.phone_number = request.POST.get('phone_number', '')
        profile.date_of_birth = request.POST.get('date_of_birth') or None
        profile.nationality = request.POST.get('nationality', '')
        profile.passport_number = request.POST.get('passport_number', '')
        profile.emergency_contact_name = request.POST.get('emergency_contact_name', '')
        profile.emergency_contact_phone = request.POST.get('emergency_contact_phone', '')
        profile.preferred_travel_style = request.POST.get('preferred_travel_style', '')
        profile.dietary_requirements = request.POST.get('dietary_requirements', '')
        profile.special_needs = request.POST.get('special_needs', '')
        profile.email_notifications = request.POST.get('email_notifications') == 'on'
        profile.marketing_emails = request.POST.get('marketing_emails') == 'on'
        profile.save()

        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('users:user_profile')

    context = {
        'user': user,
        'profile': profile,
        'page_title': 'Edit Profile',
    }

    return render(request, 'users/edit_profile.html', context)


@login_required
def change_password(request):
    """
    Change user password
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('users:user_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)

    context = {
        'form': form,
        'page_title': 'Change Password',
    }

    return render(request, 'users/change_password.html', context)


@login_required
def booking_history(request):
    """
    Detailed booking history for the user
    """
    user = request.user
    bookings = Booking.objects.filter(user=user).order_by('-created_at')

    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        bookings = bookings.filter(
            Q(package__name__icontains=search_query) |
            Q(booking_reference__icontains=search_query) |
            Q(package__main_destination__name__icontains=search_query)
        )

    context = {
        'bookings': bookings,
        'status_filter': status_filter,
        'search_query': search_query,
        'page_title': 'Booking History',
    }

    return render(request, 'users/booking_history.html', context)


@login_required
def bucket_list_view(request):
    """
    User's travel bucket list
    """
    user = request.user
    bucket_list = BucketList.objects.filter(user=user).order_by('-created_at')

    # Filter by item type if provided
    item_type = request.GET.get('type')
    if item_type:
        bucket_list = bucket_list.filter(item_type=item_type)

    context = {
        'bucket_list': bucket_list,
        'item_type': item_type,
        'page_title': 'My Bucket List',
    }

    return render(request, 'users/bucket_list.html', context)


@login_required
def add_to_bucket_list(request):
    """
    Add item to user's bucket list via AJAX
    """
    if request.method == 'POST':
        item_type = request.POST.get('item_type')
        item_id = request.POST.get('item_id')
        notes = request.POST.get('notes', '')
        priority = request.POST.get('priority', 'medium')

        try:
            # Check if item already exists in bucket list
            existing_item = None
            if item_type == 'package':
                existing_item = BucketList.objects.filter(user=request.user, package_id=item_id).first()
            elif item_type == 'accommodation':
                existing_item = BucketList.objects.filter(user=request.user, accommodation_id=item_id).first()
            elif item_type == 'destination':
                existing_item = BucketList.objects.filter(user=request.user, destination_id=item_id).first()

            if existing_item:
                return JsonResponse({'success': False, 'message': 'Item already in your bucket list!'})

            # Create new bucket list item
            bucket_item = BucketList.objects.create(
                user=request.user,
                item_type=item_type,
                notes=notes,
                priority=priority
            )

            # Set the appropriate foreign key
            if item_type == 'package':
                bucket_item.package_id = item_id
            elif item_type == 'accommodation':
                bucket_item.accommodation_id = item_id
            elif item_type == 'destination':
                bucket_item.destination_id = item_id

            bucket_item.save()

            return JsonResponse({'success': True, 'message': 'Added to your bucket list!'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@login_required
def remove_from_bucket_list(request, item_id):
    """
    Remove item from user's bucket list
    """
    try:
        bucket_item = BucketList.objects.get(id=item_id, user=request.user)
        bucket_item.delete()
        messages.success(request, 'Item removed from your bucket list!')
    except BucketList.DoesNotExist:
        messages.error(request, 'Item not found in your bucket list.')

    return redirect('users:bucket_list')


@login_required
def booking_detail(request, booking_reference):
    """
    Detailed view of a specific booking
    """
    booking = get_object_or_404(Booking, booking_reference=booking_reference, user=request.user)

    context = {
        'booking': booking,
        'page_title': f'Booking {booking.booking_reference}',
    }

    return render(request, 'users/booking_detail.html', context)

def generate_user_friendly_error_message(error_report):
    """
    Generate user-friendly error messages based on error report
    """
    messages = []

    # Check for SSL/TLS issues in development
    if (error_report['environment']['debug_mode'] and
        (error_report['confirmation_email'].get('error_type') == 'ssl_error' or
         error_report['admin_email'].get('error_type') == 'ssl_error')):
        messages.append("Email notifications couldn't be sent due to SSL certificate verification. This is normal in development - your quote request has been saved and our team will contact you.")

    # Check for authentication issues
    elif (error_report['confirmation_email'].get('error_type') == 'authentication' or
          error_report['admin_email'].get('error_type') == 'authentication'):
        messages.append("Email service temporarily unavailable due to authentication issues. Your quote request has been saved and our team will contact you.")

    # Check for connection issues
    elif (error_report['confirmation_email'].get('error_type') == 'connection' or
          error_report['admin_email'].get('error_type') == 'connection'):
        messages.append("Email service temporarily unavailable. Your quote request has been saved and our team will contact you.")

    # Generic fallback
    else:
        messages.append("Your quote request has been submitted successfully! We will contact you within 24 hours with a personalized quote.")

    # Add specific recommendations for production issues
    if not error_report['environment']['debug_mode'] and not error_report['overall_success']:
        messages.append("Please contact us directly at info@myriad-travel.com if you don't receive a confirmation email.")

    return messages


def quote_request_view(request):
    """
    Handle quote request form submission and display with comprehensive error reporting
    """
    import logging
    logger = logging.getLogger(__name__)

    # Check if package_id is provided in URL parameters
    package_id = request.GET.get('package_id')
    package = None
    if package_id:
        try:
            package = Package.objects.get(id=package_id, status=Package.PUBLISHED)
            logger.info(f"Quote request for package: {package.name} (ID: {package.id})")
        except Package.DoesNotExist:
            logger.warning(f"Invalid package ID provided: {package_id}")
            messages.warning(request, "The selected package is no longer available. You can still submit a general quote request.")

    if request.method == 'POST':
        form = QuoteRequestForm(request.POST, request=request)
        if form.is_valid():
            from .antispam import check_form_submission
            if not check_form_submission(request, form.cleaned_data.get('email', '')):
                form.add_error(None, 'We have received several requests recently. Please wait a little before submitting again.')
                return render(request, 'users/quote_form.html', {'form': form, 'package': package})
            try:
                # Create quote request
                quote_request = form.save()
                logger.info(f"Quote request created: ID {quote_request.id} for {quote_request.full_name}")

                # Associate with package if provided
                if package:
                    quote_request.package = package
                    quote_request.save()
                    logger.info(f"Quote request {quote_request.id} associated with package {package.name}")

                # Send email notifications synchronously using Mailtrap HTTP API
                try:
                    from users.tasks import send_quote_request_emails

                    # Send emails synchronously
                    result = send_quote_request_emails(quote_request.id)

                    if result.get('success'):
                        logger.info(f"Quote request emails sent successfully: quote_id={quote_request.id}")
                    else:
                        logger.warning(f"Some quote request emails failed: quote_id={quote_request.id}")

                except Exception as email_error:
                    logger.error(f"Failed to send email for quote {quote_request.id}: {email_error}")
                    # Don't fail the entire request if email sending fails - user still gets confirmation

                # Show success message - simple pattern like Novustell
                messages.success(request, "Thank you! Your quote request has been submitted successfully. We will contact you within 24 hours with a personalized quote.")
                logger.info(f"Quote request {quote_request.id} submitted successfully")

                # Redirect to success page
                return redirect('users:quote_success')

            except Exception as e:
                # Handle unexpected errors during quote request processing
                logger.error(f"Unexpected error processing quote request: {e}")
                messages.error(request, "There was an unexpected error processing your request. Please try again or contact us directly.")
                # Don't redirect, show form again

        else:
            logger.warning(f"Quote request form validation failed: {form.errors}")
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-populate form if package is specified
        initial_data = {}
        if package:
            initial_data['destination'] = package.main_destination.name if package.main_destination else ''
            logger.info(f"Pre-populating quote form with destination: {initial_data['destination']}")

        form = QuoteRequestForm(initial=initial_data)

    context = {
        'form': form,
        'package': package,
        'page_title': 'Request a Quote',
        'debug_mode': settings.DEBUG,  # Pass debug mode for template conditional logic
    }

    return render(request, 'users/quote_form.html', context)


def quote_success(request):
    """
    Success page after quote request submission
    """
    return render(request, 'users/quote_success.html', {
        'page_title': 'Quote Request Submitted',
    })


def trip_feedback(request, token):
    feedback = get_object_or_404(TripFeedback, token=token)

    if request.method == 'POST':
        form = TripFeedbackForm(request.POST, instance=feedback)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.mark_submitted()
            feedback.save()
            messages.success(request, 'Thank you. Your trip feedback has been saved for our team to review.')
            return redirect('users:trip_feedback', token=feedback.token)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = TripFeedbackForm(instance=feedback)

    return render(request, 'users/trip_feedback.html', {
        'feedback_request': feedback,
        'form': form,
        'page_title': 'Trip Feedback',
    })


# Note: send_quote_request_emails() function moved to users/tasks.py
# and is now imported directly where needed


def test_500_error(request):
    """
    Test view to trigger a 500 error for testing purposes
    Only works when DEBUG=False
    """
    raise Exception("This is a test 500 error for testing error pages")
