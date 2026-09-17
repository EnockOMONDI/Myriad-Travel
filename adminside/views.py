from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView
from .models import (
    Destination,
    Accommodation,
    TravelMode,
    Package,
    Itinerary,
    ItineraryDay,
    PackageBooking
)

# Destination Views
def destination_list(request):
    """List all destinations with hierarchy"""
    countries = Destination.objects.filter(
        destination_type=Destination.COUNTRY,
        is_active=True
    ).prefetch_related(
        Prefetch(
            'children',
            queryset=Destination.objects.filter(is_active=True).prefetch_related(
                Prefetch(
                    'children',
                    queryset=Destination.objects.filter(is_active=True)
                )
            )
        )
    ).order_by('display_order', 'name')

    context = {
        'countries': countries,
        'page_title': 'Destinations'
    }
    return render(request, 'adminside/destination_list.html', context)

def destination_detail(request, slug):
    """Detail view for a specific destination"""
    destination = get_object_or_404(
        Destination.objects.select_related('parent').prefetch_related('children'),
        slug=slug,
        is_active=True
    )

    # Get packages for this destination and its children
    destination_ids = [destination.id] + [child.id for child in destination.get_all_children()]
    packages = Package.objects.filter(
        main_destination_id__in=destination_ids,
        status=Package.PUBLISHED
    ).select_related('main_destination').prefetch_related('available_accommodations')[:12]

    # Get accommodations for this destination and its children
    accommodations = Accommodation.objects.filter(
        destination_id__in=destination_ids,
        is_active=True
    ).select_related('destination')[:12]

    context = {
        'destination': destination,
        'packages': packages,
        'accommodations': accommodations,
        'page_title': destination.name
    }
    return render(request, 'adminside/destination_detail.html', context)

# Package Views
def package_list(request):
    """Enhanced package list with modern filtering and AJAX support"""
    packages = Package.objects.filter(status=Package.PUBLISHED).select_related('main_destination', 'category')

    # Get filter parameters
    category_slug = request.GET.get('category', 'all')
    destination_id = request.GET.get('destination')
    search_query = request.GET.get('search', '').strip()

    # Category filtering using the new PackageCategory model
    if category_slug != 'all':
        packages = packages.filter(category__slug=category_slug, category__is_active=True)

    # Filter by specific destination if provided
    if destination_id:
        try:
            destination = Destination.objects.get(id=destination_id, is_active=True)
            destination_ids = [destination.id] + [child.id for child in destination.get_all_children()]
            packages = packages.filter(main_destination_id__in=destination_ids)
        except Destination.DoesNotExist:
            pass

    # Search functionality
    if search_query:
        packages = packages.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(main_destination__name__icontains=search_query) |
            Q(inclusions__icontains=search_query)
        )

    # Handle AJAX requests for dynamic filtering
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string

        # Pagination for AJAX
        paginator = Paginator(packages, 12)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        html = render_to_string('adminside/package_cards.html', {
            'page_obj': page_obj,
            'request': request
        })

        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_count': paginator.count
        })

    # Regular pagination for non-AJAX requests
    paginator = Paginator(packages, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get package categories from the PackageCategory model
    from .models import PackageCategory

    # Build categories list with counts
    categories = [
        {'key': 'all', 'name': 'All Packages', 'count': Package.objects.filter(status=Package.PUBLISHED).count()}
    ]

    # Add active package categories
    for cat in PackageCategory.objects.filter(is_active=True).order_by('display_order'):
        categories.append({
            'key': cat.slug,
            'name': cat.name,
            'count': Package.objects.filter(status=Package.PUBLISHED, category=cat).count()
        })

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_slug,
        'current_destination_id': destination_id,
        'search_query': search_query,
        'page_title': 'Travel Packages - Mbugani Luxe Adventures',
        'meta_description': 'Discover luxury safari packages and adventure tours with Mbugani Luxe Adventures. Explore Uganda, Kenya, Tanzania and more with our premium travel experiences.'
    }
    return render(request, 'adminside/package_list.html', context)

def package_detail(request, slug):
    """Detail view for a specific package"""
    package = get_object_or_404(
        Package.objects.select_related('main_destination').prefetch_related(
            'available_accommodations',
            'available_travel_modes',
            'itinerary__days__destination',
            'itinerary__days__accommodation'
        ),
        slug=slug,
        status=Package.PUBLISHED
    )

    context = {
        'package': package,
        'page_title': package.name
    }
    return render(request, 'adminside/package_detail.html', context)

# Accommodation Views
def accommodation_list(request):
    """List accommodations with filtering by destination hierarchy"""
    accommodations = Accommodation.objects.filter(is_active=True).select_related('destination')

    # Filter by destination if provided
    destination_id = request.GET.get('destination')
    if destination_id:
        try:
            destination = Destination.objects.get(id=destination_id, is_active=True)
            # Include accommodations from this destination and all its children
            destination_ids = [destination.id] + [child.id for child in destination.get_all_children()]
            accommodations = accommodations.filter(destination_id__in=destination_ids)
        except Destination.DoesNotExist:
            pass

    # Filter by accommodation type
    accommodation_type = request.GET.get('type')
    if accommodation_type:
        accommodations = accommodations.filter(accommodation_type=accommodation_type)

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        accommodations = accommodations.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(destination__name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(accommodations, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get destination hierarchy for sidebar
    countries = Destination.objects.filter(
        destination_type=Destination.COUNTRY,
        is_active=True
    ).prefetch_related(
        Prefetch(
            'children',
            queryset=Destination.objects.filter(is_active=True).prefetch_related(
                Prefetch(
                    'children',
                    queryset=Destination.objects.filter(is_active=True)
                )
            )
        )
    ).order_by('display_order', 'name')

    context = {
        'page_obj': page_obj,
        'countries': countries,
        'current_destination_id': destination_id,
        'current_type': accommodation_type,
        'search_query': search_query,
        'accommodation_types': Accommodation.ACCOMMODATION_TYPES,
        'page_title': 'Accommodations'
    }
    return render(request, 'adminside/accommodation_list.html', context)

def accommodation_detail(request, slug):
    """Detail view for a specific accommodation"""
    accommodation = get_object_or_404(
        Accommodation.objects.select_related('destination'),
        slug=slug,
        is_active=True
    )

    # Get related packages that include this accommodation
    related_packages = Package.objects.filter(
        available_accommodations=accommodation,
        status=Package.PUBLISHED
    ).select_related('main_destination')[:6]

    context = {
        'accommodation': accommodation,
        'related_packages': related_packages,
        'page_title': accommodation.name
    }
    return render(request, 'adminside/accommodation_detail.html', context)

# Travel Mode Views
def travel_mode_list(request):
    """List travel modes"""
    travel_modes = TravelMode.objects.filter(is_active=True)

    # Filter by transport type
    transport_type = request.GET.get('type')
    if transport_type:
        travel_modes = travel_modes.filter(transport_type=transport_type)

    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        travel_modes = travel_modes.filter(
            Q(name__icontains=search_query) |
            Q(departure_location__icontains=search_query) |
            Q(arrival_location__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(travel_modes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'current_type': transport_type,
        'search_query': search_query,
        'transport_types': TravelMode.TRANSPORT_TYPES,
        'page_title': 'Travel Options'
    }
    return render(request, 'adminside/travel_mode_list.html', context)

# AJAX Views for dynamic filtering
def get_destinations_ajax(request):
    """AJAX endpoint to get destinations hierarchy"""
    parent_id = request.GET.get('parent_id')

    if parent_id:
        destinations = Destination.objects.filter(
            parent_id=parent_id,
            is_active=True
        ).order_by('display_order', 'name')
    else:
        destinations = Destination.objects.filter(
            destination_type=Destination.COUNTRY,
            is_active=True
        ).order_by('display_order', 'name')

    data = [{
        'id': dest.id,
        'name': dest.name,
        'type': dest.destination_type,
        'has_children': dest.children.filter(is_active=True).exists()
    } for dest in destinations]

    return JsonResponse({'destinations': data})

def get_packages_by_destination_ajax(request):
    """AJAX endpoint to get packages filtered by destination"""
    destination_id = request.GET.get('destination_id')

    if destination_id:
        try:
            destination = Destination.objects.get(id=destination_id, is_active=True)
            destination_ids = [destination.id] + [child.id for child in destination.get_all_children()]
            packages = Package.objects.filter(
                main_destination_id__in=destination_ids,
                status=Package.PUBLISHED
            ).select_related('main_destination')[:20]
        except Destination.DoesNotExist:
            packages = Package.objects.none()
    else:
        packages = Package.objects.filter(status=Package.PUBLISHED).select_related('main_destination')[:20]

    data = [{
        'id': pkg.id,
        'name': pkg.name,
        'slug': pkg.slug,
        'destination': pkg.main_destination.name,
        'duration_days': pkg.duration_days,
        'adult_price': pkg.adult_price,
        'image_url': pkg.featured_image.cdn_url if pkg.featured_image else None
    } for pkg in packages]

    return JsonResponse({'packages': data})

def get_accommodations_by_destination_ajax(request):
    """AJAX endpoint to get accommodations filtered by destination"""
    destination_id = request.GET.get('destination_id')

    if destination_id:
        try:
            destination = Destination.objects.get(id=destination_id, is_active=True)
            destination_ids = [destination.id] + [child.id for child in destination.get_all_children()]
            accommodations = Accommodation.objects.filter(
                destination_id__in=destination_ids,
                is_active=True
            ).select_related('destination')[:20]
        except Destination.DoesNotExist:
            accommodations = Accommodation.objects.none()
    else:
        accommodations = Accommodation.objects.filter(is_active=True).select_related('destination')[:20]

    data = [{
        'id': acc.id,
        'name': acc.name,
        'slug': acc.slug,
        'type': acc.accommodation_type,
        'destination': acc.destination.name,
        'price_per_room': acc.price_per_room_per_night,
        'rating': float(acc.rating),
        'image_url': acc.image.cdn_url if acc.image else None
    } for acc in accommodations]

    return JsonResponse({'accommodations': data})


def user_package_list(request):
    """User-friendly package list with enhanced navigation"""
    # Get all countries with their hierarchical structure
    countries = Destination.objects.filter(
        destination_type=Destination.COUNTRY,
        is_active=True
    ).prefetch_related(
        Prefetch(
            'children',
            queryset=Destination.objects.filter(is_active=True).prefetch_related(
                Prefetch(
                    'children',
                    queryset=Destination.objects.filter(is_active=True)
                )
            )
        )
    ).order_by('display_order', 'name')

    # Get all published packages with their destinations and categories
    packages = Package.objects.filter(
        status=Package.PUBLISHED
    ).select_related(
        'main_destination',
        'category'
    ).prefetch_related(
        'available_accommodations',
        'available_travel_modes'
    ).order_by('-is_featured', 'main_destination__name', 'name')

    # Apply search filter if provided
    search_query = request.GET.get('search', '').strip()
    if search_query:
        packages = packages.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(main_destination__name__icontains=search_query)
        )

    # Apply destination filter if provided
    destination_id = request.GET.get('destination')
    if destination_id:
        try:
            destination = Destination.objects.get(id=destination_id)
            # Include packages for this destination and all its children
            destination_ids = [destination.id] + [child.id for child in destination.get_all_children()]
            packages = packages.filter(
                main_destination_id__in=destination_ids
            ).distinct()
        except Destination.DoesNotExist:
            pass

    context = {
        'packages': packages,
        'countries': countries,
        'search_query': search_query,
        'current_destination_id': destination_id,
        'page_title': 'Holiday Packages'
    }

    return render(request, 'adminside/user_package_list.html', context)