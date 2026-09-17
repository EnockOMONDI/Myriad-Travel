"""
Custom template tags for image handling with placeholder support and currency formatting
"""
from django import template
from django.templatetags.static import static
from django.utils.safestring import mark_safe
from decimal import Decimal
import re

register = template.Library()

def is_valid_uploadcare_url(url):
    """
    Check if a URL is a valid Uploadcare URL with actual content
    """
    if not url or not isinstance(url, str):
        return False

    # Check if it's a proper Uploadcare URL pattern
    uploadcare_pattern = r'^https://ucarecdn\.com/[a-f0-9-]+/'
    if not re.match(uploadcare_pattern, url):
        return False

    # Check for common invalid patterns
    invalid_patterns = [
        r'/00000000-0000-0000-0000-000000000000/',  # All zeros UUID
        r'/-/$',  # Empty UUID ending
        r'/None/',  # Literal "None" in URL
        r'/null/',  # Literal "null" in URL
        r'/12345678-1234-1234-1234-123456789\d+/',  # Fake test UUIDs pattern
    ]

    for pattern in invalid_patterns:
        if re.search(pattern, url):
            return False

    # Additional check for fake/test UUIDs that follow the pattern 12345678-1234-1234-1234-123456789XXX
    fake_uuid_pattern = r'/12345678-1234-1234-1234-123456789\d{3}/'
    if re.search(fake_uuid_pattern, url):
        return False

    return True

def is_valid_django_url(url):
    """
    Check if a URL is a valid Django image URL
    """
    if not url or not isinstance(url, str):
        return False

    # Basic validation for Django media URLs
    return url.startswith('/') or url.startswith('http')

@register.simple_tag
def image_with_placeholder(image_field, css_class="", alt_text="", placeholder_path="images/mbuganiluxeadventuresplaceholder.svg", lazy_load=True):
    """
    Template tag to display an image with automatic placeholder fallback

    Usage:
    {% load image_tags %}
    {% image_with_placeholder destination.image "img-fluid" "Destination Image" %}
    """
    image_url = None

    # Try Uploadcare image first
    if image_field and hasattr(image_field, 'cdn_url'):
        cdn_url = getattr(image_field, 'cdn_url', None)
        if is_valid_uploadcare_url(cdn_url):
            image_url = cdn_url

    # Try regular Django image field if Uploadcare failed
    if not image_url and image_field and hasattr(image_field, 'url'):
        django_url = getattr(image_field, 'url', None)
        if is_valid_django_url(django_url):
            image_url = django_url

    # Use placeholder if no valid image found
    if not image_url:
        image_url = static(placeholder_path)

    css_classes = f'class="{css_class}"' if css_class else ''
    alt_attribute = f'alt="{alt_text}"' if alt_text else 'alt="Image"'
    loading_attribute = 'loading="lazy"' if lazy_load else ''

    html = f'<img src="{image_url}" {css_classes} {alt_attribute} {loading_attribute}>'
    return mark_safe(html)

@register.simple_tag
def image_with_default(image_field, content_type="default", css_class="", alt_text="", use_placeholder=False):
    """
    Template tag to display an image with centralized default image fallback

    Usage:
    {% load image_tags %}
    {% image_with_default destination.image "destinations" "img-fluid" "Destination Image" %}
    {% image_with_default accommodation.image "accommodations" "img-fluid" "Accommodation Image" %}
    {% image_with_default job.image "job_listings" "img-fluid" "Job Image" %}
    """
    from django.conf import settings

    image_url = None

    # Try Uploadcare image first
    if image_field and hasattr(image_field, 'cdn_url'):
        cdn_url = getattr(image_field, 'cdn_url', None)
        if is_valid_uploadcare_url(cdn_url):
            image_url = cdn_url

    # Try regular Django image field if Uploadcare failed
    if not image_url and image_field and hasattr(image_field, 'url'):
        django_url = getattr(image_field, 'url', None)
        if is_valid_django_url(django_url):
            image_url = django_url

    # Use centralized default image system if no valid image found
    if not image_url:
        default_images_config = getattr(settings, 'DEFAULT_IMAGES', {})

        if use_placeholder:
            # Use SVG placeholder
            placeholder_path = default_images_config.get('PLACEHOLDER_SVG', 'images/mbuganiluxeadventuresplaceholder.svg')
            image_url = static(placeholder_path)
        else:
            # Use content-type specific default
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

            # Get the appropriate default image
            if config_key in default_images_config:
                default_path = default_images_config[config_key]
            else:
                default_path = default_images_config.get('DEFAULT', 'assets/images/logo/websitelogo.png')

            image_url = static(default_path)

    css_classes = f'class="{css_class}"' if css_class else ''
    alt_attribute = f'alt="{alt_text}"' if alt_text else 'alt="Image"'

    html = f'<img src="{image_url}" {css_classes} {alt_attribute}>'
    return mark_safe(html)

@register.simple_tag
def image_url_with_placeholder(image_field, placeholder_path="images/mbuganiluxeadventuresplaceholder.svg"):
    """
    Template tag to get image URL with automatic placeholder fallback

    Usage:
    {% load image_tags %}
    {% image_url_with_placeholder destination.image %}
    """
    # Try Uploadcare image first
    if image_field and hasattr(image_field, 'cdn_url'):
        cdn_url = getattr(image_field, 'cdn_url', None)
        if is_valid_uploadcare_url(cdn_url):
            return cdn_url

    # Try regular Django image field if Uploadcare failed
    if image_field and hasattr(image_field, 'url'):
        django_url = getattr(image_field, 'url', None)
        if is_valid_django_url(django_url):
            return django_url

    # Use placeholder if no valid image found
    return static(placeholder_path)

@register.simple_tag
def image_url_with_default(image_field, content_type="default", use_placeholder=False):
    """
    Template tag to get image URL with centralized default image fallback

    Usage:
    {% load image_tags %}
    {% image_url_with_default destination.image "destinations" %}
    {% image_url_with_default package.featured_image "packages" %}
    """
    from django.conf import settings

    # Try Uploadcare image first
    if image_field and hasattr(image_field, 'cdn_url'):
        cdn_url = getattr(image_field, 'cdn_url', None)
        if is_valid_uploadcare_url(cdn_url):
            return cdn_url

    # Try regular Django image field if Uploadcare failed
    if image_field and hasattr(image_field, 'url'):
        django_url = getattr(image_field, 'url', None)
        if is_valid_django_url(django_url):
            return django_url

    # Use centralized default image system if no valid image found
    default_images_config = getattr(settings, 'DEFAULT_IMAGES', {})

    if use_placeholder:
        # Use SVG placeholder
        placeholder_path = default_images_config.get('PLACEHOLDER_SVG', 'images/mbuganiluxeadventuresplaceholder.svg')
        return static(placeholder_path)
    else:
        # Use content-type specific default
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

        # Get the appropriate default image
        if config_key in default_images_config:
            default_path = default_images_config[config_key]
        else:
            default_path = default_images_config.get('DEFAULT', 'assets/images/logo/websitelogo.png')

        return static(default_path)

@register.filter
def has_image(image_field):
    """
    Template filter to check if an image field has a valid image

    Usage:
    {% load image_tags %}
    {% if destination.image|has_image %}
        <!-- Image exists -->
    {% else %}
        <!-- No image, will use placeholder -->
    {% endif %}
    """
    # Check Uploadcare image first
    if image_field and hasattr(image_field, 'cdn_url'):
        cdn_url = getattr(image_field, 'cdn_url', None)
        if is_valid_uploadcare_url(cdn_url):
            return True

    # Check regular Django image field
    if image_field and hasattr(image_field, 'url'):
        django_url = getattr(image_field, 'url', None)
        if is_valid_django_url(django_url):
            return True

    return False

@register.filter
def currency_format(value):
    """
    Format a decimal value as currency with proper formatting

    Usage:
    {% load image_tags %}
    {{ destination.starting_price|currency_format }}
    """
    if not value or value == "":
        return ""

    try:
        # Convert to Decimal if it's not already
        if not isinstance(value, Decimal):
            value = Decimal(str(value))

        # Format with commas for thousands and no decimal places for whole numbers
        if value % 1 == 0:
            # Whole number - no decimal places
            return f"${value:,.0f}"
        else:
            # Has decimal places - show 2 decimal places
            return f"${value:,.2f}"
    except (ValueError, TypeError, Exception):
        return ""

@register.filter
def split(value, delimiter=","):
    """
    Split a string by delimiter and return a list

    Usage:
    {% load image_tags %}
    {% for item in amenities|split:"," %}
        {{ item }}
    {% endfor %}
    """
    if not value:
        return []

    try:
        return [item.strip() for item in str(value).split(delimiter) if item.strip()]
    except (AttributeError, TypeError):
        return []
