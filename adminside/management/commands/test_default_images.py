from django.core.management.base import BaseCommand
from django.conf import settings
from django.templatetags.static import static
from adminside.models import Destination, Accommodation
import os


class Command(BaseCommand):
    help = 'Test default image configuration for destinations and accommodations'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🖼️  Testing Default Image Configuration'))
        self.stdout.write('=' * 60)
        
        # Test DEFAULT_IMAGES configuration
        self.test_default_images_config()
        
        # Test model methods
        self.test_model_methods()
        
        # Test file existence
        self.test_file_existence()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Default image configuration test completed!'))

    def test_default_images_config(self):
        """Test that DEFAULT_IMAGES setting is properly configured"""
        self.stdout.write('\n📋 Testing DEFAULT_IMAGES Configuration:')
        
        default_images = getattr(settings, 'DEFAULT_IMAGES', {})
        
        if not default_images:
            self.stdout.write(self.style.ERROR('❌ DEFAULT_IMAGES setting not found'))
            return
        
        expected_keys = ['DESTINATIONS', 'ACCOMMODATIONS', 'PACKAGES', 'BLOG_POSTS']
        
        for key in expected_keys:
            if key in default_images:
                path = default_images[key]
                self.stdout.write(f'✅ {key}: {path}')
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  {key}: Not configured'))

    def test_model_methods(self):
        """Test that model get_image_url methods work correctly"""
        self.stdout.write('\n🔧 Testing Model Methods:')
        
        # Test Destination model
        try:
            destination = Destination.objects.first()
            if destination:
                image_url = destination.get_image_url()
                self.stdout.write(f'✅ Destination.get_image_url(): {image_url}')
                
                # Test with no image
                if not destination.image:
                    expected_default = '/static/images/hero/discover-kenya.jpeg'
                    if image_url == expected_default:
                        self.stdout.write('✅ Destination fallback working correctly')
                    else:
                        self.stdout.write(self.style.WARNING(f'⚠️  Expected {expected_default}, got {image_url}'))
            else:
                self.stdout.write(self.style.WARNING('⚠️  No destinations found to test'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Destination test failed: {e}'))
        
        # Test Accommodation model
        try:
            accommodation = Accommodation.objects.first()
            if accommodation:
                image_url = accommodation.get_image_url()
                self.stdout.write(f'✅ Accommodation.get_image_url(): {image_url}')
                
                # Test with no image
                if not accommodation.image:
                    expected_default = '/static/images/placeholders/myriad-package-placeholder.png'
                    if image_url == expected_default:
                        self.stdout.write('✅ Accommodation fallback working correctly')
                    else:
                        self.stdout.write(self.style.WARNING(f'⚠️  Expected {expected_default}, got {image_url}'))
            else:
                self.stdout.write(self.style.WARNING('⚠️  No accommodations found to test'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Accommodation test failed: {e}'))

    def test_file_existence(self):
        """Test that default image files actually exist"""
        self.stdout.write('\n📁 Testing File Existence:')
        
        default_images = getattr(settings, 'DEFAULT_IMAGES', {})
        
        for key, path in default_images.items():
            if key in ['DESTINATIONS', 'ACCOMMODATIONS']:
                full_path = os.path.join(settings.BASE_DIR, 'static', path)
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    self.stdout.write(f'✅ {key}: {path} ({file_size:,} bytes)')
                else:
                    self.stdout.write(self.style.ERROR(f'❌ {key}: {path} - File not found'))
