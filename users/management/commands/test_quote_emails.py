"""
Django management command to test quote request email functionality
Usage: python manage.py test_quote_emails [--real-emails]
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from users.models import QuoteRequest
from users.views import send_quote_request_emails
import os


class Command(BaseCommand):
    help = 'Test quote request email functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--real-emails',
            action='store_true',
            help='Send real emails instead of using console backend',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='test@example.com',
            help='Email address to use for testing (default: test@example.com)',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up test quote requests after testing',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🌍 Testing Mbugani Luxe Adventures Quote Request Emails')
        )
        
        # Check if real emails should be used
        if options['real_emails']:
            os.environ['ENABLE_REAL_EMAILS'] = 'true'
            self.stdout.write(
                self.style.WARNING('📧 Real emails will be sent!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('📧 Using console backend (emails printed to console)')
            )

        # Display current configuration
        self.stdout.write('\n📋 Current Email Configuration:')
        self.stdout.write(f'   Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'   Host: {settings.EMAIL_HOST}')
        self.stdout.write(f'   From: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'   Admin: {settings.ADMIN_EMAIL}')

        # Create test quote request
        self.stdout.write('\n📝 Creating test quote request...')
        try:
            quote_request = QuoteRequest.objects.create(
                full_name="Test User - Management Command",
                email=options['email'],
                phone_number="+254701234567",
                destination="Maasai Mara National Reserve",
                preferred_travel_dates="December 2024",
                number_of_travelers=2,
                special_requests="This is a test quote request created by management command. Please ignore."
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Quote request created: ID {quote_request.id}')
            )
            
        except Exception as e:
            raise CommandError(f'Failed to create quote request: {e}')

        # Test email sending
        self.stdout.write('\n📤 Testing email sending...')
        try:
            result = send_quote_request_emails(quote_request)
            
            if result['overall_success']:
                self.stdout.write(
                    self.style.SUCCESS('✅ Emails sent successfully!')
                )
                self.stdout.write(f'   Confirmation email: {"✅" if result["confirmation_email"]["sent"] else "❌"}')
                self.stdout.write(f'   Admin notification: {"✅" if result["admin_email"]["sent"] else "❌"}')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Email sending failed!')
                )
                
                # Show errors
                if result['confirmation_email']['error_message']:
                    self.stdout.write(f'   Confirmation error: {result["confirmation_email"]["error_message"]}')
                    
                if result['admin_email']['error_message']:
                    self.stdout.write(f'   Admin error: {result["admin_email"]["error_message"]}')
            
            # Show warnings and recommendations
            if result['warnings']:
                self.stdout.write('\n⚠️  Warnings:')
                for warning in result['warnings']:
                    self.stdout.write(f'   - {warning}')
                    
            if result['recommendations']:
                self.stdout.write('\n💡 Recommendations:')
                for rec in result['recommendations']:
                    self.stdout.write(f'   - {rec}')
                    
        except Exception as e:
            raise CommandError(f'Failed to send emails: {e}')

        # Cleanup if requested
        if options['cleanup']:
            self.stdout.write('\n🧹 Cleaning up test data...')
            try:
                quote_request.delete()
                self.stdout.write(
                    self.style.SUCCESS('✅ Test quote request deleted')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Failed to cleanup: {e}')
                )
        else:
            self.stdout.write(
                f'\n💡 Test quote request ID {quote_request.id} was left in database'
            )
            self.stdout.write('   Use --cleanup flag to automatically delete test data')

        # Final instructions
        self.stdout.write('\n🎯 Next Steps:')
        if options['real_emails']:
            self.stdout.write('   - Check your email inbox for test emails')
            self.stdout.write('   - Verify admin email at info@mbuganiluxeadventures.com')
        else:
            self.stdout.write('   - Use --real-emails flag to test actual email sending')
        self.stdout.write('   - Test the quote form on the website')
        self.stdout.write('   - Monitor production logs for email errors')
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Email functionality test completed!')
        )
