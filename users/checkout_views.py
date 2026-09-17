"""
Modern checkout views for Mbugani Luxe Adventures
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from decimal import Decimal
import json
import random
import string

from adminside.models import Package, Accommodation, TravelMode
from .models import Booking
from .cart import Cart
from .checkout_forms import CheckoutForm
from .form_persistence import get_form_manager


def add_to_cart(request, package_id):
    """
    Add package to cart (Step 1: Package Selection)
    """
    package = get_object_or_404(Package, id=package_id, status=Package.PUBLISHED)
    cart = Cart(request)
    form_manager = get_form_manager(request)

    # Pre-populate form with saved data
    initial_data = form_manager.get_form_initial_data('package_selection')

    if request.method == 'POST':
        adults = int(request.POST.get('adults', 1))
        children = int(request.POST.get('children', 0))
        rooms = int(request.POST.get('rooms', 1))

        # Save form data for persistence
        form_data = {
            'package_id': package_id,
            'adults': adults,
            'children': children,
            'rooms': rooms
        }
        form_manager.save_form_data('package_selection', form_data)

        cart.add_package(package, adults=adults, children=children, rooms=rooms, override_quantity=True)
        messages.success(request, f'{package.name} added to your booking!')

        return redirect('users:checkout_customize', package_id=package.id)

    context = {
        'package': package,
        'initial_data': initial_data,
        'page_title': f'Book {package.name}'
    }
    return render(request, 'users/checkout/add_to_cart.html', context)


def checkout_customize(request, package_id):
    """
    Customize booking with accommodations and travel modes (Step 2)
    """
    package = get_object_or_404(Package, id=package_id, status=Package.PUBLISHED)
    cart = Cart(request)
    form_manager = get_form_manager(request)

    # Get available accommodations and travel modes for this package
    accommodations = package.available_accommodations.filter(is_active=True)
    travel_modes = package.available_travel_modes.filter(is_active=True)

    # Ensure package is in cart
    cart_items = cart.get_cart_items()
    package_in_cart = any(item['package'].id == package_id for item in cart_items)
    if not package_in_cart:
        # Add package to cart with default values if not present
        cart.add_package(package, adults=1, children=0, rooms=1)
    
    if request.method == 'POST':
        # Clear existing selections first
        cart_item = None
        for item in cart.get_cart_items():
            if item['package'].id == package_id:
                cart_item = item
                break

        if cart_item:
            # Clear existing accommodations and travel modes
            for acc in cart_item['accommodations']:
                cart.remove_accommodation(package_id, acc.id)
            for travel in cart_item['travel_modes']:
                cart.remove_travel_mode(package_id, travel.id)

        # Handle accommodation selections
        selected_accommodations = request.POST.getlist('accommodations')
        for acc_id in selected_accommodations:
            cart.add_accommodation(package_id, int(acc_id))

        # Handle custom accommodation
        custom_accommodation = request.POST.get('custom_accommodation', '').strip()
        cart.set_custom_accommodation(package_id, custom_accommodation)

        # Handle travel mode selections
        selected_travel_modes = request.POST.getlist('travel_modes')
        for travel_id in selected_travel_modes:
            cart.add_travel_mode(package_id, int(travel_id))

        # Handle self-drive option
        self_drive = request.POST.get('self_drive') == 'on'
        cart.set_self_drive(package_id, self_drive)

        # Save customization data for persistence
        customization_data = {
            'package_id': package_id,
            'selected_accommodations': selected_accommodations,
            'custom_accommodation': custom_accommodation,
            'selected_travel_modes': selected_travel_modes,
            'self_drive': self_drive
        }
        form_manager.save_form_data('customization', customization_data)

        return redirect('users:checkout_details')
    
    # Get current cart item for this package
    cart_item = None
    for item in cart.get_cart_items():
        if item['package'].id == package_id:
            cart_item = item
            break
    
    context = {
        'package': package,
        'accommodations': accommodations,
        'travel_modes': travel_modes,
        'cart_item': cart_item,
        'page_title': 'Customize Your Trip'
    }
    return render(request, 'users/checkout/customize.html', context)


def checkout_details(request):
    """
    Collect guest information (Step 3)
    """
    cart = Cart(request)
    cart_items = cart.get_cart_items()
    form_manager = get_form_manager(request)

    if not cart_items:
        messages.error(request, 'Your cart is empty. Please select a package first.')
        return redirect('users:all_packages')

    # Get existing checkout data from both old session and new form persistence
    checkout_data = request.session.get('checkout_data', {})
    saved_form_data = form_manager.get_form_initial_data('details', CheckoutForm)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Save to both old session system (for compatibility) and new form persistence
            form_data = {
                'full_name': form.cleaned_data['full_name'],
                'email': form.cleaned_data['email'],
                'phone_number': form.cleaned_data['phone_number'],
                'special_requests': form.cleaned_data['special_requests'],
                'travel_date': form.cleaned_data['travel_date'].isoformat() if form.cleaned_data['travel_date'] else None,
                'terms_accepted': form.cleaned_data['terms_accepted'],
                'marketing_consent': form.cleaned_data['marketing_consent'],
            }

            # Store in old session system for compatibility
            request.session['checkout_data'] = form_data

            # Store in new form persistence system
            form_manager.save_form_instance_data('details', form)

            return redirect('users:checkout_summary')
    else:
        # Pre-populate form with saved data (prioritize new system, fallback to old)
        initial_data = saved_form_data or {}

        # Fallback to old session data if new system has no data
        if not initial_data and checkout_data:
            initial_data = {
                'full_name': checkout_data.get('full_name', ''),
                'email': checkout_data.get('email', ''),
                'phone_number': checkout_data.get('phone_number', ''),
                'special_requests': checkout_data.get('special_requests', ''),
                'terms_accepted': checkout_data.get('terms_accepted', False),
                'marketing_consent': checkout_data.get('marketing_consent', False),
            }
            # Handle travel_date conversion from ISO string
            if checkout_data.get('travel_date'):
                try:
                    from datetime import datetime
                    initial_data['travel_date'] = datetime.fromisoformat(checkout_data['travel_date']).date()
                except (ValueError, TypeError):
                    pass

        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart_items': cart_items,
        'total_price': cart.get_total_price(),
        'page_title': 'Your Details'
    }
    return render(request, 'users/checkout/details.html', context)


def checkout_summary(request):
    """
    Review booking summary (Step 4)
    """
    cart = Cart(request)
    cart_items = cart.get_cart_items()
    checkout_data = request.session.get('checkout_data')

    if not cart_items or not checkout_data:
        messages.error(request, 'Please complete all previous steps.')
        return redirect('users:checkout_details')

    if request.method == 'POST':
        action = request.POST.get('action', 'confirm')

        if action == 'edit_details':
            # Redirect back to details page with data preserved
            return redirect('users:checkout_details')
        elif action == 'confirm':
            try:
                # Create the booking
                booking = create_booking_from_cart(cart, checkout_data)

                # Send confirmation emails (with error handling)
                try:
                    send_booking_confirmation_email(booking, is_new_user=False)
                except Exception as e:
                    # Log the error but don't fail the booking
                    print(f"Failed to send confirmation email: {e}")
                    messages.warning(request, 'Booking created successfully, but confirmation email could not be sent. You will receive a confirmation shortly.')

                try:
                    send_admin_notification_email(booking)
                except Exception as e:
                    # Log the error but don't fail the booking
                    print(f"Failed to send admin notification: {e}")

                # Clear cart and checkout data only after successful booking
                cart.clear()
                clear_checkout_session(request)

                return redirect('users:booking_confirmation', booking_reference=booking.booking_reference)

            except Exception as e:
                # Handle booking creation errors
                print(f"Booking creation failed: {e}")
                messages.error(request, 'There was an error processing your booking. Please try again or contact support.')
                return redirect('users:checkout_summary')

    context = {
        'cart_items': cart_items,
        'checkout_data': checkout_data,
        'total_price': cart.get_total_price(),
        'page_title': 'Review Your Booking'
    }
    return render(request, 'users/checkout/summary.html', context)


def clear_checkout_session(request):
    """
    Clear all checkout-related session data including form persistence
    """
    # Clear old session data
    session_keys_to_clear = ['checkout_data']
    for key in session_keys_to_clear:
        if key in request.session:
            del request.session[key]

    # Clear new form persistence data
    form_manager = get_form_manager(request)
    form_manager.clear_form_data()


def remove_from_cart(request, package_id):
    """
    Remove a package from the cart
    """
    cart = Cart(request)
    cart.remove_package(package_id)
    messages.success(request, 'Package removed from your booking.')

    # Check if cart is empty
    if not cart.get_cart_items():
        # Clear checkout data if cart is empty
        clear_checkout_session(request)
        return redirect('users:all_packages')

    # Redirect back to summary if there are still items
    return redirect('users:checkout_summary')


def update_cart_item(request, package_id):
    """
    Update cart item details (adults, children, rooms)
    """
    if request.method == 'POST':
        cart = Cart(request)
        package = get_object_or_404(Package, id=package_id, status=Package.PUBLISHED)

        adults = int(request.POST.get('adults', 1))
        children = int(request.POST.get('children', 0))
        rooms = int(request.POST.get('rooms', 1))

        # Update the cart item
        cart.add_package(package, adults=adults, children=children, rooms=rooms, override_quantity=True)
        messages.success(request, f'Updated details for {package.name}')

        return redirect('users:checkout_summary')

    return redirect('users:checkout_summary')


def booking_confirmation(request, booking_reference):
    """
    Booking confirmation page (Step 5)
    """
    booking = get_object_or_404(Booking, booking_reference=booking_reference)
    
    # Generate WhatsApp link
    whatsapp_message = f"Booking made for {booking.package.name} - Reference: {booking.booking_reference}"
    whatsapp_link = f"https://api.whatsapp.com/send?phone=254798197430&text={whatsapp_message}"
    
    context = {
        'booking': booking,
        'whatsapp_link': whatsapp_link,
        'page_title': 'Booking Confirmed'
    }
    return render(request, 'users/checkout/confirmation.html', context)


def create_booking_from_cart(cart, checkout_data):
    """
    Create a booking from cart data
    """
    cart_items = cart.get_cart_items()
    
    # For now, handle single package bookings (can be extended for multiple packages)
    cart_item = cart_items[0]
    package = cart_item['package']
    
    # Calculate pricing
    package_price = Decimal(str(package.adult_price)) * cart_item['adults']
    if cart_item['children'] > 0:
        child_price = Decimal(str(package.adult_price)) * Decimal('0.7')
        package_price += child_price * cart_item['children']
    
    accommodation_price = Decimal('0')
    for accommodation in cart_item['accommodations']:
        accommodation_price += Decimal(str(accommodation.price_per_room_per_night)) * cart_item['rooms'] * package.duration_days
    
    travel_price = Decimal('0')
    for travel_mode in cart_item['travel_modes']:
        travel_price += Decimal(str(travel_mode.price_per_person)) * (cart_item['adults'] + cart_item['children'])
    
    total_amount = package_price + accommodation_price + travel_price
    
    # Create or get user
    user = None
    user_created = False

    try:
        # Get the most recent user with this email (in case of duplicates)
        user = User.objects.filter(email=checkout_data['email']).order_by('-date_joined').first()
    except Exception as e:
        print(f"Error finding user: {e}")

    if not user:
        try:
            # Create new user with secure generated password (12 chars: letters, numbers, symbols)
            password_chars = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(random.choices(password_chars, k=12))

            # Generate unique username based on email
            base_username = checkout_data['email'].split('@')[0]
            # Clean username to only contain valid characters
            base_username = ''.join(c for c in base_username if c.isalnum() or c in '_-')
            if not base_username:
                base_username = 'user'

            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # Parse full name safely
            name_parts = checkout_data['full_name'].strip().split()
            first_name = name_parts[0] if name_parts else 'Guest'
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

            user = User.objects.create_user(
                username=username,
                email=checkout_data['email'],
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            user_created = True

            # Send welcome email with password (only for new users)
            try:
                send_welcome_email(user, password)
            except Exception as e:
                print(f"Failed to send welcome email: {e}")

        except Exception as e:
            print(f"Error creating user: {e}")
            # If user creation fails, we can still proceed with booking
            # The booking will be created without a user association
            pass
    
    # Prepare special requests with custom options
    special_requests = checkout_data.get('special_requests', '')

    # Add custom accommodation to special requests if present
    if cart_item.get('custom_accommodation'):
        custom_acc_text = f"\n\nCustom Accommodation Request:\n{cart_item['custom_accommodation']}"
        special_requests += custom_acc_text

    # Add self-drive note to special requests if selected
    if cart_item.get('self_drive'):
        self_drive_text = "\n\nTransportation: Self-drive / Own transportation selected"
        special_requests += self_drive_text

    # Create booking
    booking = Booking.objects.create(
        package=package,
        user=user,
        full_name=checkout_data['full_name'],
        email=checkout_data['email'],
        phone_number=checkout_data['phone_number'],
        number_of_adults=cart_item['adults'],
        number_of_children=cart_item['children'],
        number_of_rooms=cart_item['rooms'],
        package_price=package_price,
        accommodation_price=accommodation_price,
        travel_price=travel_price,
        total_amount=total_amount,
        special_requests=special_requests.strip(),
        travel_date=checkout_data.get('travel_date'),
    )
    
    # Add selected accommodations and travel modes
    booking.selected_accommodations.set(cart_item['accommodations'])
    booking.selected_travel_modes.set(cart_item['travel_modes'])

    # Send booking confirmation email
    try:
        send_booking_confirmation_email(booking, is_new_user=user_created)
    except Exception as e:
        print(f"Failed to send booking confirmation email: {e}")

    return booking


def send_booking_confirmation_email(booking, is_new_user=False):
    """
    Send booking confirmation email to customer using Mailtrap HTTP API
    """
    try:
        from users.tasks import send_email_via_mailtrap

        subject = f'Booking Confirmation - {booking.booking_reference}'

        # URL encode the WhatsApp message
        from urllib.parse import quote
        whatsapp_message = f"Booking made for {booking.package.name} - Reference: {booking.booking_reference}"
        whatsapp_link = f"https://api.whatsapp.com/send?phone=254798197430&text={quote(whatsapp_message)}"

        # Generate dashboard URL
        dashboard_url = f"{getattr(settings, 'SITE_URL', 'https://mbuganiluxeadventures.com')}/profile/"

        html_message = render_to_string('users/emails/booking_confirmation.html', {
            'booking': booking,
            'whatsapp_link': whatsapp_link,
            'is_new_user': is_new_user,
            'dashboard_url': dashboard_url,
        })

        email_sent = send_email_via_mailtrap(
            subject=subject,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.email],
        )

        if email_sent:
            booking.confirmation_email_sent = True
            booking.save()
        else:
            raise Exception("Failed to send email via Mailtrap API")

    except Exception as e:
        print(f"Error sending booking confirmation email: {e}")
        raise


def send_admin_notification_email(booking):
    """
    Send booking notification to admin using Mailtrap HTTP API
    """
    from users.tasks import send_email_via_mailtrap

    subject = f'New Booking Received - {booking.booking_reference}'

    html_message = render_to_string('users/emails/admin_notification.html', {
        'booking': booking,
    })

    email_sent = send_email_via_mailtrap(
        subject=subject,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
    )

    if email_sent:
        booking.admin_notification_sent = True
        booking.save()


def send_welcome_email(user, password):
    """
    Send welcome email to new user with login credentials using Mailtrap HTTP API
    """
    from users.tasks import send_email_via_mailtrap

    subject = 'Welcome to Mbugani Luxe Adventures'

    html_message = render_to_string('users/emails/welcome.html', {
        'user': user,
        'password': password,
    })

    send_email_via_mailtrap(
        subject=subject,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
