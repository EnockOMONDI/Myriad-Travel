"""
Context processors for Mbugani Luxe Adventures Django project.
Provides global template variables and default image management.
"""

from django.conf import settings
from django.templatetags.static import static


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
            return default_images_urls.get('DEFAULT', static('assets/images/logo/websitelogo.png'))
    
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
            return default_images_urls.get('PLACEHOLDER_SVG', static('images/mbuganiluxeadventuresplaceholder.svg'))
        
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
        'DEBUG': getattr(settings, 'DEBUG', False),
    }
