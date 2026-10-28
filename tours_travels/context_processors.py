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

    kenya_destination_aliases = {
        'Mombasa': ('mombasa-north-coast',),
        'Diani': ('diani-beach',),
        'Malindi': ('malindi',),
        'Watamu': ('watamu',),
        'Kilifi': ('kilifi',),
        'Lamu': ('lamu',),
        'Maasai Mara': ('maasai-mara-national-reserve', 'masai-mara-national-reserve'),
        'Nakuru': ('nakuru',),
        'Amboseli': ('amboseli-national-park',),
        'Samburu': ('samburu-national-reserve',),
        'Tsavo': ('tsavo-east-national-park', '07-tsavo-east-watamu-malindi'),
        'Nairobi': ('nairobi',),
        'Naivasha': ('naivasha',),
        'Elementaita': ('naivasha-and-elementaita',),
        'Baringo / Bogoria': ('great-rift-valley', 'great-rift-valley-naivasha'),
        'Mt. Kenya': ('mount-kenya', 'mount-kenya-national-park'),
        'Kajiado': ('kajiado-county',),
        'Kisumu': ('kisumu',),
        'Longonot': ('longonot',),
        'Machakos': ('machakos',),
        'Kajiado / Suswa': ('kajiado-suswa',),
        'Sagana': ('sagana',),
    }
    world_destination_aliases = {
        'Tanzania': ('tanzania',), 'Uganda': ('uganda',), 'Rwanda': ('rwanda',),
        'Egypt': ('egypt',), 'South Africa': ('south-africa',), 'Morocco': ('morocco',),
        'Namibia': ('namibia',), 'Zimbabwe': ('zimbabwe',),
        'USA': ('united-states',), 'Canada': ('canada',), 'Brazil': ('brazil',),
        'Caribbean Islands': ('caribbean-islands', 'caribbean'),
        'Germany': ('germany',), 'England': ('england',), 'Italy': ('italy',),
        'France': ('france',), 'Spain': ('spain',), 'Greece': ('greece',), 'Turkey': ('turkey',),
        'China': ('china',), 'Thailand': ('thailand',), 'India': ('india',), 'Singapore': ('singapore',),
        'Dubai': ('dubai',), 'Abu Dhabi': ('abu-dhabi',), 'Israel': ('israel',),
        'Saudi Arabia': ('saudi-arabia',), 'Jordan': ('jordan',), 'Oman': ('oman',),
        'Zanzibar': ('zanzibar',), 'Seychelles': ('seychelles',), 'Mauritius': ('mauritius',),
        'Maldives': ('maldives',), 'Madagascar': ('madagascar',),
    }

    def destination_items(queryset, limit=6):
        return [
            {'label': destination.name, 'url': reverse('users:destination_detail', kwargs={'slug': destination.slug})}
            for destination in queryset[:limit]
        ]

    kenya_destinations_by_slug = None

    def kenya_named_items(labels, fallback_url):
        nonlocal kenya_destinations_by_slug
        if kenya_destinations_by_slug is None:
            kenya_destinations_by_slug = {
                destination.slug: destination
                for destination in Destination.objects.filter(
                    is_active=True,
                    show_in_navigation=True,
                    region='kenya',
                ).order_by('-is_featured', 'display_order', 'name')
            }
        items = []
        for label in labels:
            destination = next(
                (kenya_destinations_by_slug.get(slug) for slug in kenya_destination_aliases.get(label, ()) if kenya_destinations_by_slug.get(slug)),
                None,
            )
            items.append({
                'label': label,
                'url': reverse('users:destination_detail', kwargs={'slug': destination.slug}) if destination else fallback_url,
            })
        return items

    world_destinations_by_slug = None

    def world_named_items(labels, fallback_url):
        nonlocal world_destinations_by_slug
        if world_destinations_by_slug is None:
            world_destinations_by_slug = {
                destination.slug: destination
                for destination in Destination.objects.filter(
                    is_active=True,
                    show_in_navigation=True,
                ).exclude(region='kenya').order_by('-is_featured', 'display_order', 'name')
            }
        return [
            {
                'label': label,
                'url': reverse('users:destination_detail', kwargs={'slug': destination.slug}) if destination else fallback_url,
            }
            for label in labels
            for destination in [next((world_destinations_by_slug.get(slug) for slug in world_destination_aliases.get(label, ()) if world_destinations_by_slug.get(slug)), None)]
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
        ('Africa', 'africa'), ('Americas', 'americas'), ('Europe', 'europe'),
        ('Asia', 'asia'), ('Indian Ocean Islands', 'indian-ocean-islands'),
        ('Middle East', 'middle-east'),
    ]
    themed_slugs = ['cruises', 'wellness-retreats', 'shopping-tours', 'religious-pilgrimages', 'honeymoon-packages']
    themed_categories = categories.filter(slug__in=themed_slugs)

    explore_kenya_url = reverse('users:explore_kenya')
    tours_safaris_url = reverse('users:tours_safaris')
    deals_url = reverse('users:deals')
    kenya_sections = [
        {'label': 'Beach', 'url': explore_kenya_url, 'items': kenya_named_items(
            ['Mombasa', 'Diani', 'Malindi', 'Watamu', 'Kilifi', 'Lamu'], explore_kenya_url,
        )},
        {'label': 'Safaris', 'url': tours_safaris_url, 'items': kenya_named_items(
            ['Maasai Mara', 'Nakuru', 'Amboseli', 'Samburu', 'Tsavo'], tours_safaris_url,
        )},
        {'label': 'Getaways', 'url': explore_kenya_url, 'items': kenya_named_items(
            ['Nairobi', 'Naivasha', 'Elementaita', 'Nakuru', 'Baringo / Bogoria', 'Mt. Kenya', 'Kajiado', 'Kisumu'], explore_kenya_url,
        )},
        {'label': 'Day Trips', 'url': explore_kenya_url, 'items': kenya_named_items(
            ['Nairobi', 'Naivasha', 'Longonot', 'Machakos', 'Kajiado / Suswa', 'Sagana'], explore_kenya_url,
        )},
        {'label': 'Seasonal Packages', 'url': deals_url, 'items': [
            {'label': label, 'url': deals_url}
            for label in ['Valentine', 'Easter Holidays', 'August Holidays', 'Mashujaa Holidays', 'Jamhuri Holidays', 'Christmas / New Year']
        ]},
    ]
    world_section_labels = {
        'Africa': ['Tanzania', 'Uganda', 'Rwanda', 'Egypt', 'South Africa', 'Morocco', 'Namibia', 'Zimbabwe'],
        'Americas': ['USA', 'Canada', 'Brazil', 'Caribbean Islands'],
        'Europe': ['Germany', 'England', 'Italy', 'France', 'Spain', 'Greece', 'Turkey'],
        'Asia': ['China', 'Thailand', 'India', 'Singapore'],
        'Middle East': ['Dubai', 'Abu Dhabi', 'Israel', 'Saudi Arabia', 'Jordan', 'Oman'],
        'Indian Ocean Islands': ['Zanzibar', 'Seychelles', 'Mauritius', 'Maldives', 'Madagascar'],
    }
    world_sections = [
        {
            'label': label,
            'url': reverse('users:explore_region', kwargs={'region': region}),
            'items': world_named_items(labels, reverse('users:explore_region', kwargs={'region': region})),
        }
        for label, region in world_regions
        if (labels := world_section_labels.get(label))
    ]
    safari_categories = categories.exclude(slug__in=themed_slugs).filter(
        Q(packages__region__in=['kenya-safari', 'kenya-coast', 'day-trips']) |
        Q(tagged_packages__region__in=['kenya-safari', 'kenya-coast', 'day-trips'])
    )
    safari_menu_content = [
        ('Wildlife Safaris', 'wildlife-safaris', 'Classic game drives, Big Five and migration experiences'),
        ('Adventure Safaris', 'adventure-safaris', 'Hiking, trekking, camping and off-the-beaten-path experiences'),
        ('Luxury Safaris', 'luxury-safaris', 'Exclusive lodges, private safaris and fly-in experiences'),
        ('Cultural Safaris', 'cultural-safaris', 'Authentic cultural and community experiences'),
        ('Photography & Birding Safaris', 'photography-birding-safaris', 'Special-interest safaris for photographers and bird enthusiasts'),
        ('Honeymoon Safaris', 'honeymoon-safaris', 'Romantic bush escapes and private experiences'),
        ('Family Safaris', 'family-safaris', 'Family-friendly itineraries and experiences'),
        ('Group Joining Safaris', 'group-joining-safaris', 'Scheduled shared departures and affordable safari packages'),
    ]
    safari_categories_by_slug = {
        category.slug: category
        for category in PackageCategory.objects.filter(
            slug__in=[slug for _, slug, _ in safari_menu_content],
            is_active=True,
            show_in_navigation=True,
        )
    }
    safari_sections = [
        {
            'label': label,
            'url': f'{tours_safaris_url}?category={slug}',
            'description': description,
            'items': [],
        }
        for label, slug, description in safari_menu_content
        if slug in safari_categories_by_slug
    ]
    theme_sections = [
        {'label': 'Travel Themes', 'url': reverse('users:themed_packages'),
         'items': category_items(themed_categories, 'themed_packages')},
    ]

    collections = TravelCollection.objects.filter(
        is_active=True, show_in_navigation=True, packages__status=Package.PUBLISHED,
    ).distinct().order_by('display_order', 'name')
    for section, target in [('themes', theme_sections)]:
        collection_items = [{'label': item.name, 'url': item.get_absolute_url()} for item in collections.filter(section=section)[:5]]
        if collection_items:
            target.append({'label': 'Featured collections', 'url': '', 'items': collection_items})

    now = timezone.now()
    today = timezone.localtime(now).date() if timezone.is_aware(now) else now.date()
    deals = Campaign.objects.filter(
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
        {'label': 'Deals', 'url': reverse('users:deals'), 'parent_clickable': True, 'sections': []},
    ]
    return {
        'public_menus': menus,
        'current_deals': deals[:8],
        'nav_explore_kenya': kenya_destinations[:5],
        'nav_explore_world': destinations.exclude(region='kenya')[:5],
        'nav_tours_safaris': safari_categories[:5],
        'nav_signature_experiences': themed_categories[:5],
    }
