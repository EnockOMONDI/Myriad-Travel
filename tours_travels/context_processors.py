"""
Context processors for Mbugani Luxe Adventures Django project.
Provides global template variables and default image management.
"""

from django.conf import settings
from django.templatetags.static import static
from django.db.models import Q


def default_images(request):
    """
    Context processor to provide default image URLs in all templates.
    
    Makes DEFAULT_IMAGES configuration available as 'default_images' in templates.
    Also provides helper functions for getting category-specific default images.
    
    Usage in templates:
    {{ default_images.DEFAULT }}
    {{ default_images.DESTINATIONS }}
    {{ default_images.get_default_for_content_type:'destinations' }}
    """
    
    # Get default images configuration from settings
    default_images_config = getattr(settings, 'DEFAULT_IMAGES', {})
    
    # Convert relative paths to full static URLs
    default_images_urls = {}
    for key, path in default_images_config.items():
        default_images_urls[key] = static(path)
    
    # Helper function to get default image for content type
    def get_default_for_content_type(content_type):
        """
        Get the appropriate default image for a specific content type.
        
        Args:
            content_type (str): The type of content (destinations, accommodations, etc.)
            
        Returns:
            str: Static URL for the default image
        """
        content_type_upper = content_type.upper()
        
        # Map content types to configuration keys
        content_type_mapping = {
            'DESTINATION': 'DESTINATIONS',
            'DESTINATIONS': 'DESTINATIONS',
            'ACCOMMODATION': 'ACCOMMODATIONS', 
            'ACCOMMODATIONS': 'ACCOMMODATIONS',
            'PACKAGE': 'PACKAGES',
            'PACKAGES': 'PACKAGES',
            'BLOG': 'BLOG_POSTS',
            'BLOG_POST': 'BLOG_POSTS',
            'BLOG_POSTS': 'BLOG_POSTS',
            'JOB': 'JOB_LISTINGS',
            'JOB_LISTING': 'JOB_LISTINGS',
            'JOB_LISTINGS': 'JOB_LISTINGS',
            'JOBS': 'JOB_LISTINGS',
        }
        
        # Get the mapped key or use the content type directly
        config_key = content_type_mapping.get(content_type_upper, content_type_upper)
        
        # Return the specific default image or fall back to general default
        if config_key in default_images_urls:
            return default_images_urls[config_key]
        else:
            return default_images_urls.get('DEFAULT', static('images/placeholders/myriad-package-placeholder.png'))
    
    # Helper function to get image URL with fallback
    def get_image_url_with_fallback(image_field, content_type='default', use_placeholder=False):
        """
        Get image URL with automatic fallback to appropriate default image.
        
        Args:
            image_field: Django image field or Uploadcare field
            content_type (str): Type of content for appropriate default
            use_placeholder (bool): Whether to use SVG placeholder instead
            
        Returns:
            str: Image URL or default image URL
        """
        # Try Uploadcare image first
        if image_field and hasattr(image_field, 'cdn_url'):
            cdn_url = getattr(image_field, 'cdn_url', None)
            if cdn_url and cdn_url.strip():
                return cdn_url
        
        # Try regular Django image field
        if image_field and hasattr(image_field, 'url'):
            try:
                django_url = getattr(image_field, 'url', None)
                if django_url and django_url.strip():
                    return django_url
            except (ValueError, AttributeError):
                pass
        
        # Use placeholder SVG if requested
        if use_placeholder:
            return default_images_urls.get('PLACEHOLDER_SVG', static('images/placeholders/myriad-package-placeholder.png'))
        
        # Use content-type specific default
        return get_default_for_content_type(content_type)
    
    # Create the context object with helper methods
    class DefaultImagesContext:
        def __init__(self, urls_dict):
            # Add all default image URLs as attributes
            for key, url in urls_dict.items():
                setattr(self, key, url)
        
        def get_default_for_content_type(self, content_type):
            return get_default_for_content_type(content_type)
        
        def get_image_url_with_fallback(self, image_field, content_type='default', use_placeholder=False):
            return get_image_url_with_fallback(image_field, content_type, use_placeholder)
    
    return {
        'default_images': DefaultImagesContext(default_images_urls),
        'get_default_image': get_default_for_content_type,
        'get_image_with_fallback': get_image_url_with_fallback,
    }


def site_settings(request):
    """
    Context processor to provide common site settings in all templates.
    """
    return {
        'SITE_URL': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        'TURNSTILE_SITE_KEY': getattr(settings, 'TURNSTILE_SITE_KEY', ''),
        'DEBUG': getattr(settings, 'DEBUG', False),
        'company': {
            'name': 'Myriad Travel',
            'tagline': 'Beyond Imagination',
            'address': {
                'full': 'Parklands, Crescent Business Center, 6th Floor, Nairobi, Kenya',
            },
            'contacts': {
                'primary_phone': '+254712236522',
                'alt_phone': '+254113446213',
                'phone_formatted': '+254 (0) 712 236 522',
                'whatsapp': '254712236522',
                'email_general': 'info@myriad-travel.com',
                'email_marketing': 'marketing@myriad-travel.com',
            },
            'socials': {
                'facebook': 'https://web.facebook.com/myriadtravelke/?_rdc=1&_rdr#',
                'instagram': 'https://www.instagram.com/myriadtravelke/',
                'tiktok': 'https://www.tiktok.com/@myriadtravel',
            },
        },
    }


def navigation_collections(request):
    """Build the public navigation from active, published travel records."""
    from django.urls import reverse
    from django.utils import timezone
    from adminside.models import Campaign, Destination, Package, PackageCategory, TravelCollection

    def destination_items(queryset, limit=6):
        return [
            {'label': destination.name, 'url': reverse('users:destination_detail', kwargs={'slug': destination.slug})}
            for destination in queryset[:limit]
        ]

    def category_items(queryset, route, limit=6):
        base_url = reverse('users:' + route)
        return [
            {'label': category.name, 'url': f'{base_url}?category={category.slug}'}
            for category in queryset[:limit]
        ]

    destinations = Destination.objects.filter(
        is_active=True,
        show_in_navigation=True,
        packages__status=Package.PUBLISHED,
    ).distinct().order_by('-is_featured', 'display_order', 'name')
    categories = PackageCategory.objects.filter(
        is_active=True,
        show_in_navigation=True,
    ).filter(
        Q(packages__status=Package.PUBLISHED) | Q(tagged_packages__status=Package.PUBLISHED)
    ).distinct().order_by('display_order', 'name')

    kenya_destinations = destinations.filter(region='kenya')
    world_regions = [
        ('Africa', 'africa'), ('Americas', 'americas'), ('Asia', 'asia'),
        ('Australasia', 'australasia'), ('Europe', 'europe'),
        ('Indian Ocean Islands', 'indian-ocean-islands'), ('Middle East', 'middle-east'),
    ]
    themed_slugs = ['cruises', 'wellness-retreats', 'shopping-tours', 'religious-pilgrimages', 'honeymoon-packages']
    themed_categories = categories.filter(slug__in=themed_slugs)

    kenya_sections = [
        {'label': 'Beach & Coast', 'url': reverse('users:explore_kenya'),
         'items': destination_items(kenya_destinations.filter(packages__region='kenya-coast'))},
        {'label': 'Safaris', 'url': reverse('users:tours_safaris'),
         'items': destination_items(kenya_destinations.filter(packages__region='kenya-safari'))},
        {'label': 'Getaways', 'url': reverse('users:explore_kenya'),
         'items': category_items(categories.filter(Q(packages__region='day-trips') | Q(tagged_packages__region='day-trips')), 'explore_kenya')},
        {'label': 'Themed Experiences', 'url': reverse('users:themed_packages'),
         'items': category_items(themed_categories, 'themed_packages')},
        {'label': 'Day Trips', 'url': reverse('users:explore_kenya'),
         'items': category_items(categories.filter(Q(packages__region='day-trips') | Q(tagged_packages__region='day-trips')), 'explore_kenya')},
    ]
    world_sections = [
        {'label': label, 'url': reverse('users:explore_the_world'),
         'items': destination_items(destinations.filter(region=region))}
        for label, region in world_regions
    ]
    safari_categories = categories.exclude(slug__in=themed_slugs).filter(
        Q(packages__region__in=['kenya-safari', 'kenya-coast', 'day-trips']) |
        Q(tagged_packages__region__in=['kenya-safari', 'kenya-coast', 'day-trips'])
    )
    safari_sections = [
        {'label': 'Safari & Adventure', 'url': reverse('users:tours_safaris'),
         'items': category_items(safari_categories, 'tours_safaris')},
        {'label': 'Destinations', 'url': reverse('users:tours_safaris'),
         'items': destination_items(kenya_destinations)},
    ]
    theme_sections = [
        {'label': 'Travel Themes', 'url': reverse('users:themed_packages'),
         'items': category_items(themed_categories, 'themed_packages')},
    ]

    collections = TravelCollection.objects.filter(
        is_active=True, show_in_navigation=True, packages__status=Package.PUBLISHED,
    ).distinct().order_by('display_order', 'name')
    for section, target in [('kenya', kenya_sections), ('world', world_sections), ('safaris', safari_sections), ('themes', theme_sections)]:
        collection_items = [{'label': item.name, 'url': item.get_absolute_url()} for item in collections.filter(section=section)[:5]]
        if collection_items:
            target.append({'label': 'Featured collections', 'url': '', 'items': collection_items})

    now = timezone.now()
    today = timezone.localtime(now).date() if timezone.is_aware(now) else now.date()
    deals = Campaign.objects.filter(
        is_active=True,
        starts_on__lte=today,
        ends_on__gte=today,
        package__status=Package.PUBLISHED,
    ).select_related('package').order_by('display_order', 'pk')
    deal_items = [
        {'label': campaign.title, 'url': reverse('users:package_detail', kwargs={'slug': campaign.package.slug})}
        for campaign in deals[:5]
    ]

    menus = [
        {'label': 'Explore Kenya', 'url': reverse('users:explore_kenya'), 'parent_clickable': False, 'sections': kenya_sections},
        {'label': 'Explore The World', 'url': reverse('users:explore_the_world'), 'parent_clickable': False, 'sections': world_sections},
        {'label': 'Tours & Safaris', 'url': reverse('users:tours_safaris'), 'parent_clickable': False, 'sections': safari_sections},
        {'label': 'Themed Experiences', 'url': reverse('users:themed_packages'), 'parent_clickable': False, 'sections': theme_sections},
        {'label': 'Deals', 'url': reverse('users:deals'), 'parent_clickable': True, 'sections': [
            {'label': 'Current offers', 'url': reverse('users:deals'), 'items': deal_items},
        ]},
        {'label': 'About Us', 'url': reverse('users:aboutus'), 'parent_clickable': True, 'sections': [
            {'label': 'About Myriad', 'url': reverse('users:aboutus'), 'items': [
                {'label': 'Our Story', 'url': reverse('users:aboutus')},
                {'label': 'Myriad Services', 'url': reverse('users:services')},
                {'label': 'Travel Blog', 'url': reverse('blog:blog-list')},
            ]},
        ]},
        {'label': 'Contact Us', 'url': reverse('users:contact'), 'parent_clickable': True, 'sections': [
            {'label': 'Talk to Myriad', 'url': reverse('users:contact'), 'items': [
                {'label': 'Contact Details', 'url': reverse('users:contact')},
                {'label': 'Request Quote', 'url': reverse('users:quote_request')},
            ]},
        ]},
    ]
    return {
        'public_menus': menus,
        'nav_explore_kenya': kenya_destinations[:5],
        'nav_explore_world': destinations.exclude(region='kenya')[:5],
        'nav_tours_safaris': safari_categories[:5],
        'nav_signature_experiences': themed_categories[:5],
    }
