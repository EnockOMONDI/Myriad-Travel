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
from django.core.paginator import Paginator
from django.urls import reverse


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
from adminside.itinerary_audit import analyse_itinerary
from django.utils.text import slugify
from django.utils.html import strip_tags
from types import SimpleNamespace
from html.parser import HTMLParser


PUBLIC_REGION_ORDER = [
    ('africa', 'Africa', 'Safaris, cities, culture and beach escapes across the continent.', 'globe-2'),
    ('americas', 'Americas', 'Big landscapes, city breaks and long-haul experiences.', 'mountain'),
    ('asia', 'Asia', 'Island stays, wellness retreats and city discoveries.', 'palmtree'),
    ('australasia', 'Australasia', 'Coastal landscapes, island escapes and wide-open journeys.', 'sun'),
    ('europe', 'Europe', 'Classic cities, cruises and seasonal European journeys.', 'building-2'),
    ('indian-ocean-islands', 'Indian Ocean Islands', 'Warm-water escapes, beaches and island holidays.', 'waves'),
    ('middle-east', 'Middle East', 'Desert cities, heritage journeys and regional escapes.', 'landmark'),
]

REGION_CARD_IMAGES = {
    'africa': '/static/images/destinations/maasai-mara-national-reserve.jpg',
    'americas': '/static/images/destinations/caribbean.jpg',
    'asia': '/static/images/destinations/ubud-bali.jpg',
    'australasia': '/static/images/destinations/australasia.jpg',
    'europe': '/static/images/destinations/mediterranean-europe.jpg',
    'indian-ocean-islands': '/static/images/destinations/maldives.jpg',
    'middle-east': '/static/images/destinations/dubai-abu-dhabi.jpg',
}


def _region_keys(region_slug):
    """Treat existing Kenya records as part of Africa without changing their data yet."""
    return ['africa', 'kenya'] if region_slug == 'africa' else [region_slug]


def _destination_tree_ids(destination):
    """Return an active destination and all active descendants without duplicating packages."""
    ids = [destination.pk]
    pending = list(destination.children.filter(is_active=True).only('pk'))
    while pending:
        child = pending.pop()
        ids.append(child.pk)
        pending.extend(child.children.filter(is_active=True).only('pk'))
    return ids


def _destination_ids_for_page(destination):
    """Include a country's linked multi-country areas without moving packages."""
    ids = set(_destination_tree_ids(destination))
    if destination.destination_type == Destination.COUNTRY and not destination.is_multi_country:
        ids.update(
            Destination.objects.filter(
                is_active=True,
                is_multi_country=True,
                member_countries=destination,
            ).values_list('id', flat=True)
        )
    return ids


def _packages_for_destinations(destination_ids):
    return _packages_for_collection().filter(
        main_destination_id__in=destination_ids,
    ).distinct()


def _region_cards():
    """Build homepage cards from current destination/package data, not hardcoded inventory."""
    cards = []
    for slug, name, description, icon in PUBLIC_REGION_ORDER:
        keys = _region_keys(slug)
        destinations = Destination.objects.filter(is_active=True, region__in=keys)
        destination_ids = list(destinations.values_list('id', flat=True))
        packages = _packages_for_collection().filter(main_destination_id__in=destination_ids)
        image_destination = destinations.exclude(image='').exclude(image__isnull=True).order_by('display_order', 'name').first()
        cards.append({
            'slug': slug,
            'name': name,
            'description': description,
            'icon': icon,
            'image': _image_url(image_destination.image, REGION_CARD_IMAGES[slug]) if image_destination else REGION_CARD_IMAGES[slug],
            'destination_count': destinations.filter(packages__status=Package.PUBLISHED).distinct().count(),
            'package_count': packages.count(),
            'url': reverse('users:explore_region', kwargs={'region': slug}),
        })
    return cards


def _homepage_destination_cards(names, limit):
    """Select destination cards by editorial preference while keeping records DB-driven."""
    destinations = list(Destination.objects.filter(is_active=True).order_by('display_order', 'name'))
    selected = []
    for requested in names:
        requested_slug = slugify(requested)
        match = next((item for item in destinations if item.slug == requested_slug), None)
        if not match:
            match = next((item for item in destinations if requested.lower() in item.name.lower()), None)
        if match and match not in selected:
            selected.append(match)
    return [_destination_presenter(item) for item in selected[:limit]]


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


# Reviewed local fallback photographs. An admin-uploaded destination or package
# image always wins; this list only prevents published pages from falling back
# to the generic Myriad placeholder while the image library is being completed.
CURATED_DESTINATION_IMAGES = {
    'akagera-national-park',
    '07-tsavo-east-watamu-malindi',
    'alaska',
    'amboseli-national-park',
    'arabian-gulf',
    'arusha',
    'cairo',
    'cape-town',
    'caribbean',
    'dar-es-salaam',
    'diani-beach',
    'dubai',
    'dubai-abu-dhabi',
    'egypt',
    'great-rift-valley',
    'great-rift-valley-naivasha',
    'israel-and-jordan',
    'johannesburg',
    'kajiado-county',
    'kibale-forest-national-park',
    'kigali',
    'kenya',
    'kwale-county',
    'lake-manyara-national-park',
    'maasai-mara-national-reserve',
    'masai-mara-national-reserve',
    'maldives',
    'marsabit-county',
    'masai-mara-and-diani',
    'mauritius',
    'mount-kilimanjaro-national-park',
    'mount-kenya',
    'mount-kenya-national-park',
    'murchison-falls-national-park',
    'mediterranean-europe',
    'matobo-national-park',
    'mombasa-north-coast',
    'nairobi',
    'naivasha',
    'naivasha-and-elementaita',
    'narok-county',
    'norwegian-fjords',
    'phuket',
    'rwanda',
    'samburu-national-reserve',
    'serengeti-national-park',
    'tarangire-national-park',
    'tanzania',
    'tsavo-east-national-park',
    'uae',
    'ubud-bali',
    'uganda',
    'zambia',
    'zanzibar',
    'zanzibar-island',
    'zimbabwe',
}


def _curated_destination_image(destination):
    slug = getattr(destination, 'slug', '')
    if slug in CURATED_DESTINATION_IMAGES:
        return f'/static/images/destinations/{slug}.jpg'
    return None


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


def _uploadcare_card_url(image_field, fallback):
    """Use a predictable card ratio instead of an admin-saved crop canvas."""
    uuid = getattr(image_field, 'uuid', None)
    if uuid:
        return f'https://ucarecdn.com/{uuid}/-/preview/1120x700/'
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
    destination_image = getattr(package.main_destination, 'image', None)
    public_image = package.featured_image or destination_image
    curated_destination_image = _curated_destination_image(package.main_destination)
    image_fallback = curated_destination_image or '/static/images/placeholders/myriad-package-placeholder.png'
    price_kes = int(package.adult_price or 0)
    price_currency = package.price_currency or 'KES'
    price_display = f'{price_currency} {price_kes:,}' if price_currency == 'USD' else f'KSh {price_kes:,}'
    highlights = [line.strip() for line in (package.highlights or '').splitlines() if line.strip()]
    region_label = package.get_region_display() if hasattr(package, 'get_region_display') else category
    lipa_months = package.lipa_pole_pole_months or 4
    departure = package.departures.filter(is_active=True).order_by('display_order', 'starts_on').first()
    special_offer = None
    if departure:
        special_offer = {
            'label': departure.label or 'Scheduled departure',
            'date': departure.date_label,
            'departure': ' '.join(filter(None, [departure.departure_location, departure.departure_time.strftime('%-I:%M %p') if departure.departure_time else ''])),
            'return': ' '.join(filter(None, [departure.return_location, departure.return_time_note])),
            'notes': [line.strip() for line in package.travel_notes.splitlines() if line.strip()],
            'packing_list': package.packing_list(),
            'before_faqs': [],
        }
    itinerary_days, itinerary_audit = _itinerary_presenter(package)
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
        'categories': [item.name for item in package.categories.all()],
        'collections': [item.name for item in package.collections.filter(is_active=True)],
        'region_label': region_label,
        'region': package.region or slugify(category) or 'kenya-safari',
        'destination': destination,
        # A package-specific upload wins. Otherwise its curated destination banner
        # supplies a coherent public image until the package gets its own asset.
        'featured_image': _uploadcare_card_url(public_image, image_fallback),
        'hero_image': _uploadcare_preview_url(public_image, image_fallback),
        'duration': f'{package.duration_days} Days / {package.duration_nights} Nights',
        'rating': package.rating,
        'reviews_count': package.total_reviews,
        'price_kes': price_kes,
        'price_currency': price_currency,
        'price_display': price_display,
        'child_price_kes': int(package.child_price or 0),
        'single_price_kes': package.single_occupancy_price or 0,
        'single_supplement_kes': package.single_occupancy_supplement or 0,
        'packing_list': package.packing_list(),
        'travel_notes': [line.strip() for line in package.travel_notes.splitlines() if line.strip()],
        'meta_title': package.meta_title,
        'meta_description': package.meta_description,
        'meta_keywords': [item.strip() for item in package.meta_keywords.split(',') if item.strip()],
        'aeo_summary': package.aeo_summary,
        'price_usd': round(price_kes / 130) if price_kes else 0,
        'lipa_pole_pole': package.lipa_pole_pole,
        'lipa_pole_pole_months': lipa_months,
        'price_kes_monthly': round(price_kes / lipa_months) if price_kes and lipa_months else 0,
        'price_usd_monthly': round((price_kes / 130) / lipa_months) if price_kes and lipa_months else 0,
        'highlights': highlights,
        'inclusions': _rich_text_items(package.inclusions),
        'exclusions': _rich_text_items(package.exclusions),
        'itinerary': itinerary_days,
        'itinerary_audit': itinerary_audit,
        'best_for': best_for,
        'route_summary': route_summary,
        'accommodations': accommodation_names,
        'transport_modes': transport_names,
        'has_image': bool(public_image or curated_destination_image),
        'special_offer': special_offer,
        'model': package,
    }


def _itinerary_presenter(package):
    audit = analyse_itinerary(package)
    days = []
    for index, day in enumerate(audit['rows'], start=1):
        days.append({
            **day,
            'date': day.get('date', ''),
            'theme': day.get('theme', ''),
            'route': day.get('route', ''),
            'summary': day.get('summary', ''),
            'main_activities': day.get('main_activities', []),
            'optional_activities': day.get('optional_activities', []),
            'overnight': day.get('overnight_location') or day.get('stay', ''),
            'operational_notes': day.get('operational_notes', ''),
        })
    return days, audit


def _public_copy(value):
    """Return only destination copy that is ready for the public site."""
    if not value:
        return ''
    normalized = strip_tags(str(value)).strip()
    lowered = normalized.casefold()
    generic_markers = (
        'travel destination for curated myriad travel experiences',
        'myriad is still confirming',
        'description being prepared',
        'content coming soon',
    )
    if any(marker in lowered for marker in generic_markers):
        return ''
    return value


def _destination_presenter(destination):
    country = destination.country.name if destination.country else ('Multi-country area' if destination.is_multi_country else 'Kenya')
    return {
        'id': destination.id,
        'name': destination.name,
        'slug': destination.slug,
        'country': country,
        'description': _public_copy(destination.meta_description or destination.description),
        'image': _image_url(
            destination.image,
            _curated_destination_image(destination) or '/static/images/placeholders/myriad-package-placeholder.png',
        ),
        'badge': 'Featured' if destination.is_featured else destination.get_destination_type_display(),
        'popular_for': ['Safari', 'Nature', 'Tailored Trips'],
        'is_multi_country': destination.is_multi_country,
        'model': destination,
    }


def _public_page_context(package_limit=None):
    packages_qs = Package.objects.select_related('main_destination', 'category').prefetch_related(
        'collections',
        'available_accommodations',
        'available_travel_modes',
        'itinerary__days',
    ).filter(status=Package.PUBLISHED).order_by('home_rank', '-is_featured', '-published_at', '-created_at')
    if package_limit:
        packages_qs = packages_qs[:package_limit]

    destinations_qs = Destination.objects.filter(
        is_active=True,
        is_featured=True,
    ).order_by('display_order', 'name')[:6]
    trip_feedbacks = TripFeedback.objects.filter(
        is_visible_on_site=True,
        permission_to_publish=True,
        status__in=[TripFeedback.SUBMITTED, TripFeedback.REVIEWED],
    ).order_by('-is_featured', '-submitted_at', '-created_at')[:6]
    return {
        'packages': [_package_presenter(package) for package in packages_qs],
        'featured_destinations': [_destination_presenter(dest) for dest in destinations_qs],
        'all_destinations': destinations_qs,
        'region_cards': _region_cards(),
        'trip_feedbacks': trip_feedbacks,
    }






def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST, request=request)

        if form.is_valid():
            from .antispam import check_form_submission
            if not check_form_submission(request, form.cleaned_data.get('email', '')):
                from .antispam import SECURITY_BLOCK_MESSAGE
                form.add_error(None, SECURITY_BLOCK_MESSAGE)
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
            from .antispam import SECURITY_BLOCK_MESSAGE
            form.add_error(None, SECURITY_BLOCK_MESSAGE)
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
                from .antispam import SECURITY_BLOCK_MESSAGE
                form.add_error(None, SECURITY_BLOCK_MESSAGE)
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
        'categories',
        'collections',
        'available_accommodations',
        'available_travel_modes',
        'itinerary__days',
    ).filter(status=Package.PUBLISHED).order_by('home_rank', '-is_featured', '-published_at', '-created_at')


def _collection_context(title, eyebrow, description, packages_qs, destination_qs=None, groups=None,
                        active_filter='all', category_filters=None, hero_image=None, show_destinations=True):
    context = _public_page_context(package_limit=4)
    packages = list(packages_qs)
    filters = []
    seen_filters = set()
    for package in packages:
        package_categories = ([package.category] if package.category else []) + list(package.categories.all())
        for category in package_categories:
            slug = slugify(category.name)
            if slug not in seen_filters:
                seen_filters.add(slug)
                filters.append({
                    'label': category.name,
                    'slug': slug,
                })
    context.update({
        'collection_title': title,
        'collection_eyebrow': eyebrow,
        'collection_description': description,
        'collection_packages': [_package_presenter(package) for package in packages],
        'collection_destinations': destination_qs or [],
        'collection_filters': category_filters if category_filters is not None else filters,
        'collection_active_filter': active_filter or 'all',
        'collection_groups': groups or [],
        'collection_hero_image': hero_image or 'images/hero/tours-safaris.jpeg',
        'collection_show_destinations': show_destinations,
    })
    return context


def _filter_collection_by_category(request, packages_qs):
    """Apply one shareable category filter and keep all eligible pills visible."""
    selected_category = request.GET.get('category', '').strip()
    categories = PackageCategory.objects.filter(
        is_active=True,
    ).filter(
        Q(packages__in=packages_qs) | Q(tagged_packages__in=packages_qs)
    ).distinct().order_by('display_order', 'name')
    filters = [{'label': category.name, 'slug': category.slug} for category in categories]
    if selected_category and selected_category != 'all':
        packages_qs = packages_qs.filter(
            Q(category__slug=selected_category) | Q(categories__slug=selected_category)
        ).distinct()
    return packages_qs, filters, selected_category or 'all'


def _render_collection(request, context):
    """Return only the package fragment for in-page collection filtering."""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'users/pages/includes/collection_package_results.html', context)
    return render(request, 'users/pages/collection.html', context)


def explore_kenya(request):
    packages_qs = _packages_for_collection().filter(region__in=['kenya-safari', 'kenya-coast', 'day-trips'])
    packages_qs, filters, selected_category = _filter_collection_by_category(request, packages_qs)
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
        active_filter=selected_category,
        category_filters=filters,
        hero_image='images/hero/discover-kenya.jpeg',
        show_destinations=False,
    )
    return _render_collection(request, context)


def explore_the_world(request):
    packages_qs = _packages_for_collection().filter(region='international').exclude(
        Q(category__slug__in=SIGNATURE_CATEGORY_SLUGS) | Q(categories__slug__in=SIGNATURE_CATEGORY_SLUGS)
    ).distinct()
    packages_qs, filters, selected_category = _filter_collection_by_category(request, packages_qs)
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
        active_filter=selected_category,
        category_filters=filters,
        hero_image='images/hero/beyond-imagination.jpeg',
    )
    context['world_region_cards'] = [card for card in _region_cards() if card['slug'] != 'australasia']
    return _render_collection(request, context)


def explore_region(request, region):
    region = region.lower()
    region_meta = next((item for item in PUBLIC_REGION_ORDER if item[0] == region), None)
    if not region_meta:
        raise Http404('Region not found')

    region_keys = _region_keys(region)
    region_destinations = Destination.objects.filter(
        is_active=True,
        region__in=region_keys,
    ).select_related('parent').distinct()
    country_filters = region_destinations.filter(
        destination_type=Destination.COUNTRY,
        is_multi_country=False,
        parent__isnull=True,
    ).order_by('display_order', 'name')
    selected_country = request.GET.get('country', '').strip()
    if selected_country:
        selected = country_filters.filter(slug=selected_country).first()
        if selected:
            destination_ids = _destination_ids_for_page(selected)
            region_destinations = Destination.objects.filter(
                is_active=True,
                id__in=destination_ids,
            ).select_related('parent')

    packages_qs = _packages_for_destinations(region_destinations.values_list('id', flat=True))
    packages_qs, filters, selected_category = _filter_collection_by_category(request, packages_qs)
    context = _collection_context(
        region_meta[1],
        'Explore region',
        region_meta[2],
        packages_qs,
        region_destinations.order_by('display_order', 'name')[:24],
        active_filter=selected_category,
        category_filters=filters,
        hero_image='images/hero/beyond-imagination.jpeg',
    )
    context.update({
        'region': region_meta,
        'region_slug': region,
        'region_image': next((card['image'] for card in _region_cards() if card['slug'] == region), '/static/images/placeholders/myriad-package-placeholder.png'),
        'country_filters': country_filters,
        'multi_country_groups': region_destinations.filter(is_multi_country=True).prefetch_related('member_countries').order_by('display_order', 'name'),
        'selected_country': selected_country,
        'region_total_destinations': region_destinations.count(),
    })
    return render(request, 'users/pages/region_detail.html', context)


def tours_safaris(request):
    packages_qs = _packages_for_collection().filter(
        Q(region__in=['kenya-safari', 'kenya-coast', 'day-trips']) |
        Q(category__slug__in=TOURS_SAFARI_CATEGORY_SLUGS)
    ).exclude(
        Q(category__slug__in=SIGNATURE_CATEGORY_SLUGS) | Q(categories__slug__in=SIGNATURE_CATEGORY_SLUGS)
    ).distinct()
    packages_qs, filters, selected_filter = _filter_collection_by_category(request, packages_qs)
    context = _collection_context(
        'Tours & Safaris',
        'Safari, coast and adventure planning',
        'Safari, coast, mountain, culture, photography and adventure trips gathered into one clear planning space. Start with a style, then open the package that fits your dates and group.',
        packages_qs,
        active_filter=selected_filter,
        category_filters=filters,
        hero_image='images/hero/tours-safaris.jpeg',
    )
    return _render_collection(request, context)


def signature_experiences(request):
    groups = []
    packages_qs = _packages_for_collection().filter(
        Q(category__slug__in=SIGNATURE_CATEGORY_SLUGS) | Q(categories__slug__in=SIGNATURE_CATEGORY_SLUGS)
    ).distinct()
    packages_qs, filters, selected_filter = _filter_collection_by_category(request, packages_qs)
    for category in PackageCategory.objects.filter(slug__in=SIGNATURE_CATEGORY_SLUGS, is_active=True).order_by('display_order', 'name'):
        group_packages = [
            pkg for pkg in packages_qs
            if pkg.category_id == category.id or category.id in [item.id for item in pkg.categories.all()]
        ]
        if group_packages:
            groups.append({
                'title': category.name,
                'description': category.description,
                'packages': [_package_presenter(package) for package in group_packages],
            })
    context = _collection_context(
        'Themed Packages',
        'Curated journeys for a specific reason to travel',
        'Cruises, wellness retreats, shopping tours, pilgrimages and honeymoon escapes prepared as ready-to-enquire Myriad Travel experiences.',
        packages_qs,
        groups=groups,
        active_filter=selected_filter,
        category_filters=filters,
        hero_image='images/hero/signature-tours.jpeg',
    )
    return render(request, 'users/pages/signature_experiences.html', context)


def travel_collection(request, slug):
    from adminside.models import TravelCollection
    collection = get_object_or_404(TravelCollection, slug=slug, is_active=True)
    packages_qs, filters, selected_filter = _filter_collection_by_category(
        request, _packages_for_collection().filter(collections=collection)
    )
    context = _collection_context(
        collection.name, collection.get_section_display(), collection.description,
        packages_qs, active_filter=selected_filter, category_filters=filters,
        hero_image='images/hero/tours-safaris.jpeg',
    )
    return _render_collection(request, context)


def deals(request):
    from django.utils import timezone

    now = timezone.now()
    today = timezone.localtime(now).date() if timezone.is_aware(now) else now.date()
    deal_campaigns = Campaign.objects.filter(
        package__status=Package.PUBLISHED,
        ends_on__gte=today,
    ).select_related('package').order_by('starts_on', 'display_order', 'pk')
    packages_qs = _packages_for_collection().filter(
        campaigns__in=deal_campaigns,
    ).distinct()
    packages_qs, filters, selected_filter = _filter_collection_by_category(request, packages_qs)
    context = _collection_context(
        'Current Deals',
        'Limited-date offers and campaigns',
        'Current Myriad offers are published here while their campaign dates are active. Open any package to request a quote and confirm availability.',
        packages_qs,
        active_filter=selected_filter,
        category_filters=filters,
    )
    context['deal_campaigns'] = deal_campaigns
    context['deal_statuses'] = {campaign.package_id: campaign.public_status for campaign in deal_campaigns}
    return _render_collection(request, context)


def destinations(request):
    destination_query = request.GET.get('destination', '').strip()
    if destination_query:
        destination = Destination.objects.filter(
            is_active=True,
        ).filter(
            Q(slug=destination_query) | Q(name__iexact=destination_query.replace('-', ' '))
        ).first()
        if destination:
            return redirect('users:destination_detail', slug=destination.slug)
    return render(request, 'users/pages/destinations.html', _public_page_context())


def destination_detail(request, slug):
    destination = get_object_or_404(Destination, slug=slug, is_active=True)
    packages_qs = _packages_for_destinations(_destination_ids_for_page(destination))
    packages_qs, filters, selected_category = _filter_collection_by_category(request, packages_qs)
    paginator = Paginator(packages_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    context = _public_page_context(package_limit=4)
    destination_region = 'africa' if destination.region == 'kenya' else destination.region
    context.update({
        'collection_eyebrow': 'Destination guide',
        'collection_filters': filters,
        'collection_active_filter': selected_category or 'all',
        'collection_packages': [_package_presenter(package) for package in page_obj.object_list],
        'collection_page_obj': page_obj,
        'collection_total_packages': paginator.count,
        'destination': _destination_presenter(destination),
        'destination_model': destination,
        'destination_children': destination.children.filter(is_active=True).order_by('display_order', 'name'),
        'destination_member_countries': destination.member_countries.filter(is_active=True).order_by('name'),
        'destination_country': destination.country,
        'destination_region': destination_region,
    })
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'users/pages/includes/destination_package_results.html', context)
    return render(request, 'users/pages/destination_detail.html', context)


def package_detail(request, slug):
    package = get_object_or_404(
        Package.objects.select_related('main_destination', 'category').prefetch_related(
            'itinerary__days',
            'available_accommodations',
            'available_travel_modes',
            'gallery_images',
        ),
        slug=slug,
        status=Package.PUBLISHED,
    )
    context = _public_page_context(package_limit=6)
    context['pkg'] = _package_presenter(package)
    context['package_has_gallery'] = any(image.is_visible for image in package.gallery_images.all())
    return render(request, 'users/pages/package_detail.html', context)


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
                from .antispam import SECURITY_BLOCK_MESSAGE
                form.add_error(None, SECURITY_BLOCK_MESSAGE)
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
                from .antispam import SECURITY_BLOCK_MESSAGE
                error_message = SECURITY_BLOCK_MESSAGE
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
        kenya_preferences = ('Chalbi', 'Maasai Mara', 'Amboseli', 'Diani', 'Watamu')
        kenya_packages = list(
            Package.objects.select_related('main_destination', 'category').prefetch_related('collections')
            .filter(status=Package.PUBLISHED)
            .order_by('home_rank', '-is_featured', '-published_at', '-created_at')
        )
        preferred_kenya = [
            item for requested in kenya_preferences
            for item in kenya_packages
            if item.main_destination and requested.lower() in item.main_destination.get_full_name().lower()
        ]
        selected_kenya = list(dict.fromkeys(preferred_kenya))[:4]
        if len(selected_kenya) < 4:
            selected_kenya.extend(item for item in kenya_packages if item not in selected_kenya)
        context['homepage_kenya_packages'] = [_package_presenter(item) for item in selected_kenya[:4]]
        context['homepage_world_destinations'] = _homepage_destination_cards(
            ('Dubai', 'South Africa', 'Egypt', 'Maldives', 'Seychelles', 'Rwanda'), 6
        )
        from adminside.models import Campaign
        from django.utils import timezone
        now = timezone.now()
        today = timezone.localtime(now).date() if timezone.is_aware(now) else now.date()
        campaigns = Campaign.objects.filter(
            is_active=True, starts_on__lte=today, ends_on__gte=today,
            package__status=Package.PUBLISHED,
        ).select_related('package__category', 'package__main_destination')[:4]
        context['current_campaigns'] = [
            {'title': campaign.title, 'travel_dates': campaign.travel_dates,
             'pkg': _package_presenter(campaign.package)} for campaign in campaigns
        ]
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
    form = UserBookingsForm(request.POST or None, request=request)
    context = {'form': form, 'package': package}

    if request.method == 'POST':
        if form.is_valid():
            from .antispam import check_form_submission
            if not check_form_submission(request, getattr(request.user, 'email', '')):
                from .antispam import SECURITY_BLOCK_MESSAGE
                form.add_error(None, SECURITY_BLOCK_MESSAGE)
                return render(request, 'users/UserBookingsForm.html', context)
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
        except (Package.DoesNotExist, ValueError, OverflowError):
            logger.warning(f"Invalid package ID provided: {package_id}")
            messages.warning(request, "The selected package is no longer available. You can still submit a general quote request.")

    if request.method == 'POST':
        form = QuoteRequestForm(request.POST, request=request)
        if form.is_valid():
            from .antispam import check_form_submission
            if not check_form_submission(request, form.cleaned_data.get('email', '')):
                from .antispam import SECURITY_BLOCK_MESSAGE
                form.add_error(None, SECURITY_BLOCK_MESSAGE)
                return render(request, 'users/quote_form.html', {'form': form, 'package': package})
            try:
                # Create quote request
                quote_request = form.save()
                logger.info(f"Quote request created: ID {quote_request.id} for {quote_request.full_name}")

                # Associate with package if provided
                if package:
                    quote_request.package = package
                    room_preference = request.POST.get('room_preference', 'sharing')
                    if room_preference not in {'sharing', 'single'}:
                        room_preference = 'sharing'
                    if room_preference == 'single' and not package.has_single_occupancy:
                        room_preference = 'sharing'
                    quote_request.room_preference = room_preference
                    rate = package.single_occupancy_price if room_preference == 'single' else package.adult_price
                    quote_request.estimated_value = rate * quote_request.number_of_travelers
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
        form = TripFeedbackForm(request.POST, instance=feedback, request=request)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.mark_submitted()
            feedback.save()
            messages.success(request, 'Thank you. Your trip feedback has been saved for our team to review.')
            return redirect('users:trip_feedback', token=feedback.token)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = TripFeedbackForm(instance=feedback, request=request)

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
