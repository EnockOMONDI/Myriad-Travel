from django.core.management.base import BaseCommand
from django.test import Client
import re


class Command(BaseCommand):
    help = 'Test H2 heading rendering in About Us page'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Testing H2 Heading Rendering'))
        self.stdout.write('=' * 60)
        
        try:
            # Create a test client
            client = Client()
            
            # Get the about us page
            response = client.get('/aboutus/')
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('✅ About Us page loads successfully'))
                
                html_content = response.content.decode('utf-8')
                
                # Check for the CTA H2 element
                cta_h2_pattern = r'<h2[^>]*>Ready for Your Luxury Safari Adventure\?</h2>'
                if re.search(cta_h2_pattern, html_content):
                    self.stdout.write(self.style.SUCCESS('✅ CTA H2 element found'))
                else:
                    self.stdout.write(self.style.ERROR('❌ CTA H2 element not found'))
                
                # Check for inline styles in CTA H2
                if 'color: #ffffff' in html_content and 'TAN-Garland-Regular' in html_content:
                    self.stdout.write(self.style.SUCCESS('✅ H2 inline styles found'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  H2 inline styles not found'))
                
                # Check for CSS rules
                if '.cta-section h2' in html_content:
                    self.stdout.write(self.style.SUCCESS('✅ CTA H2 CSS rules found'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  CTA H2 CSS rules not found'))
                
                # Check for font fallbacks
                if 'Georgia' in html_content and 'Times New Roman' in html_content:
                    self.stdout.write(self.style.SUCCESS('✅ Font fallbacks found'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Font fallbacks not found'))
                
                # Check for text shadow
                if 'text-shadow' in html_content:
                    self.stdout.write(self.style.SUCCESS('✅ Text shadow enhancement found'))
                else:
                    self.stdout.write(self.style.WARNING('⚠️  Text shadow enhancement not found'))
                
                # Count all H2 elements
                h2_count = html_content.count('<h2')
                self.stdout.write(f'📊 Total H2 elements found: {h2_count}')
                
                # Check for problematic CSS rules
                if '.h2 {' in html_content:
                    self.stdout.write(self.style.ERROR('❌ Problematic .h2 CSS rule still present'))
                else:
                    self.stdout.write(self.style.SUCCESS('✅ No problematic .h2 CSS rules found'))
                
            else:
                self.stdout.write(self.style.ERROR(f'❌ Page failed to load (Status: {response.status_code})'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Test failed: {e}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ H2 rendering test completed!'))
