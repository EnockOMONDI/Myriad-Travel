from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.utils import timezone
from adminside.models import Package, Destination
from users.models import Booking, NewsletterSubscription, JobApplication
import os


class Command(BaseCommand):
    help = 'Test all email templates for Mbugani Luxe Adventures branding'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('📧 Testing Email Templates'))
        self.stdout.write('=' * 60)
        
        # Test all email templates
        self.test_booking_confirmation()
        self.test_welcome_email()
        self.test_newsletter_confirmation()
        self.test_job_application_emails()
        self.test_admin_notification()
        
        self.stdout.write(self.style.SUCCESS('\n✅ Email template testing completed!'))

    def test_booking_confirmation(self):
        """Test booking confirmation email template"""
        self.stdout.write('\n📋 Testing Booking Confirmation Email:')
        
        try:
            # Create mock data
            user = User(
                username='testuser',
                email='test@example.com',
                first_name='John',
                last_name='Doe'
            )
            
            # Mock booking data
            booking_data = {
                'booking_reference': 'MLA-2024-001',
                'full_name': 'John Doe',
                'email': 'test@example.com',
                'phone_number': '+2540701810167',
                'number_of_adults': 2,
                'number_of_children': 1,
                'number_of_rooms': 1,
                'total_amount': 150000,
                'created_at': timezone.now(),
                'package': {
                    'name': 'Maasai Mara Safari Adventure',
                    'duration_days': 3,
                    'main_destination': {'name': 'Maasai Mara'}
                },
                'special_requests': 'Vegetarian meals preferred'
            }
            
            # Render template
            html_content = render_to_string('users/emails/booking_confirmation.html', {
                'booking': type('MockBooking', (), booking_data)(),
                'user': user,
                'is_new_user': False
            })
            
            # Check for Mbugani branding
            if 'Mbugani Luxe Adventures' in html_content:
                self.stdout.write('✅ Company name: Mbugani Luxe Adventures found')
            else:
                self.stdout.write(self.style.ERROR('❌ Company name not found'))
            
            if '+254 798 197 430' in html_content:
                self.stdout.write('✅ Updated phone number found')
            else:
                self.stdout.write(self.style.WARNING('⚠️  Updated phone number not found'))
            
            if '#291c1b' in html_content or '#fb9300' in html_content:
                self.stdout.write('✅ Mbugani brand colors found')
            else:
                self.stdout.write(self.style.WARNING('⚠️  Brand colors not found'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Booking confirmation test failed: {e}'))

    def test_welcome_email(self):
        """Test welcome email template"""
        self.stdout.write('\n👋 Testing Welcome Email:')
        
        try:
            user = User(
                username='newuser',
                email='newuser@example.com',
                first_name='Jane',
                last_name='Smith'
            )
            
            html_content = render_to_string('users/emails/welcome.html', {
                'user': user,
                'password': 'temppassword123'
            })
            
            if 'Mbugani Luxe Adventures' in html_content:
                self.stdout.write('✅ Welcome email branding correct')
            else:
                self.stdout.write(self.style.ERROR('❌ Welcome email branding incorrect'))
                
            if '+254 798 197 430' in html_content:
                self.stdout.write('✅ Welcome email phone number updated')
            else:
                self.stdout.write(self.style.WARNING('⚠️  Welcome email phone number not updated'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Welcome email test failed: {e}'))

    def test_newsletter_confirmation(self):
        """Test newsletter confirmation email template"""
        self.stdout.write('\n📰 Testing Newsletter Confirmation Email:')
        
        try:
            subscription_data = {
                'email': 'subscriber@example.com',
                'travel_tips': True,
                'special_offers': True,
                'destination_updates': True
            }
            
            html_content = render_to_string('users/emails/newsletter_confirmation.html', {
                'subscription': type('MockSubscription', (), subscription_data)()
            })
            
            if 'Mbugani Luxe Adventures' in html_content:
                self.stdout.write('✅ Newsletter branding correct')
            else:
                self.stdout.write(self.style.ERROR('❌ Newsletter branding incorrect'))
                
            if '+254 798 197 430' in html_content:
                self.stdout.write('✅ Newsletter phone number updated')
            else:
                self.stdout.write(self.style.WARNING('⚠️  Newsletter phone number not updated'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Newsletter confirmation test failed: {e}'))

    def test_job_application_emails(self):
        """Test job application email templates"""
        self.stdout.write('\n💼 Testing Job Application Emails:')
        
        try:
            application_data = {
                'full_name': 'Alex Johnson',
                'email': 'alex@example.com',
                'phone_number': '+2540701810167',
                'position': 'tour_guide',
                'experience_years': 3,
                'cover_letter': 'I am passionate about wildlife and tourism...',
                'created_at': timezone.now()
            }
            
            # Test confirmation email
            html_content = render_to_string('users/emails/job_application_confirmation.html', {
                'application': type('MockApplication', (), {
                    **application_data,
                    'get_position_display': lambda: 'Tour Guide'
                })()
            })
            
            if 'Mbugani Luxe Adventures' in html_content:
                self.stdout.write('✅ Job application branding correct')
            else:
                self.stdout.write(self.style.ERROR('❌ Job application branding incorrect'))
                
            if '+254 798 197 430' in html_content:
                self.stdout.write('✅ Job application phone number updated')
            else:
                self.stdout.write(self.style.WARNING('⚠️  Job application phone number not updated'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Job application test failed: {e}'))

    def test_admin_notification(self):
        """Test admin notification email template"""
        self.stdout.write('\n🚨 Testing Admin Notification Email:')
        
        try:
            booking_data = {
                'booking_reference': 'MLA-2024-002',
                'full_name': 'Test Customer',
                'email': 'customer@example.com',
                'phone_number': '+2540701810167',
                'number_of_adults': 2,
                'number_of_children': 0,
                'number_of_rooms': 1,
                'total_amount': 200000,
                'created_at': timezone.now(),
                'package': {
                    'name': 'Serengeti Migration Safari',
                    'duration_days': 5,
                    'main_destination': {'name': 'Serengeti'}
                },
                'get_status_display': lambda: 'Pending',
                'special_requests': 'Early morning game drives preferred'
            }
            
            html_content = render_to_string('users/emails/admin_notification.html', {
                'booking': type('MockBooking', (), booking_data)()
            })
            
            if 'Mbugani Luxe Adventures' in html_content:
                self.stdout.write('✅ Admin notification branding correct')
            else:
                self.stdout.write(self.style.ERROR('❌ Admin notification branding incorrect'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Admin notification test failed: {e}'))

    def check_template_exists(self, template_path):
        """Check if template file exists"""
        from django.template.loader import get_template
        try:
            get_template(template_path)
            return True
        except:
            return False
