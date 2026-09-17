from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse
import re


class Command(BaseCommand):
    help = 'Test that the About Us page Our Inspiration section has the correct background image'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🖼️  Testing About Us Background Image'))
        self.stdout.write('=' * 60)
        
        try:
            # Create a test client
            client = Client()
            
            # Get the about us page
            response = client.get('/aboutus/')
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('✅ About Us page loads successfully'))
                
                # Check if the background image is in the HTML
                html_content = response.content.decode('utf-8')
                
                # Look for the inspiration section with background image
                if 'assets/images/hero/3.png' in html_content:
                    self.stdout.write(self.style.SUCCESS('✅ Background image (hero/3.png) found in HTML'))
                else:
                    self.stdout.write(self.style.ERROR('❌ Background image not found in HTML'))
                
                # Check for the gradient overlay
                if 'rgba(93, 0, 0, 0.8)' in html_content and 'rgba(251, 147, 0, 0.6)' in html_content:
                    self.stdout.write(self.style.SUCCESS('✅ Mbugani brand gradient overlay found'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Brand gradient overlay not found'))
                
                # Check for the inspiration section
                if 'inspiration-section' in html_content:
                    self.stdout.write(self.style.SUCCESS('✅ Our Inspiration section found'))
                else:
                    self.stdout.write(self.style.ERROR('❌ Our Inspiration section not found'))
                
                # Check for the Mbugani meaning content
                if 'Mbugani means' in html_content:
                    self.stdout.write(self.style.SUCCESS('✅ Mbugani meaning content found'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Mbugani meaning content not found'))
                
                self.stdout.write('\n📊 Summary:')
                self.stdout.write(f'   - Page Status: {response.status_code}')
                self.stdout.write(f'   - Content Length: {len(html_content):,} characters')
                
            else:
                self.stdout.write(self.style.ERROR(f'❌ About Us page failed to load (Status: {response.status_code})'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Test failed with error: {e}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Background image test completed!'))
