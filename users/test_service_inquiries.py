from types import SimpleNamespace
from unittest.mock import Mock, patch
import requests
from django.test import SimpleTestCase, RequestFactory, override_settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages import get_messages
from django.utils.html import conditional_escape
from django.contrib.auth import get_user_model
from django.urls import reverse
from users import views
from users.tasks import send_email_via_mailtrap
from users.inquiry_email import send_service_inquiry_emails


@override_settings(DEFAULT_FROM_EMAIL='Myriad <info@example.com>', ADMIN_EMAIL='admin@example.com', MICE_INQUIRY_EMAIL='admin@example.com', MAILTRAP_API_TOKEN='test-token', EMAIL_PROVIDER='mailtrap')
class ServiceInquiryTests(SimpleTestCase):
    def request(self):
        request = RequestFactory().post('/mice/', {})
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_all_three_forms_save_once_and_redirect_after_mail_failure(self):
        for view, form_name in [(views.micepage, 'MICEInquiryForm'), (views.student_travel, 'StudentTravelInquiryForm'), (views.ngo_travel, 'NGOTravelInquiryForm')]:
            with self.subTest(form=form_name), patch('users.views.' + form_name) as form_class, patch('users.antispam.check_form_submission', return_value=True), patch('users.inquiry_email.send_service_inquiry_emails', return_value=False):
                form = form_class.return_value
                form.is_valid.return_value = True
                form.cleaned_data = {'email': 'qa@example.com'}
                request = self.request()
                response = view(request)
                self.assertEqual(response.status_code, 302)
                form.save.assert_called_once()
                self.assertIn('saved', str(list(get_messages(request))[0]))

    def test_invalid_form_does_not_save_or_send(self):
        with patch('users.views.MICEInquiryForm') as form_class, patch('users.views.render') as render, patch('users.inquiry_email.send_service_inquiry_emails') as send:
            form_class.return_value.is_valid.return_value = False
            views.micepage(self.request())
            form_class.return_value.save.assert_not_called()
            send.assert_not_called()
            render.assert_called_once()

    def test_valid_submission_success_message(self):
        with patch('users.views.MICEInquiryForm') as form_class, patch('users.antispam.check_form_submission', return_value=True), patch('users.inquiry_email.send_service_inquiry_emails', return_value=True):
            form_class.return_value.cleaned_data = {'email': 'qa@example.com'}
            request = self.request()
            response = views.micepage(request)
            self.assertEqual(response.status_code, 302)
            self.assertIn('successfully', str(list(get_messages(request))[0]))

    def test_notifications_route_to_admin_and_customer_and_escape_input(self):
        inquiry = SimpleNamespace(pk=42, contact_person='QA', email='qa@example.com', event_details='<script>alert(1)</script>')
        form = SimpleNamespace(fields={'event_details': SimpleNamespace(label='Details')})
        with patch('users.inquiry_email.send_email_via_mailtrap', return_value=True) as send:
            self.assertTrue(send_service_inquiry_emails(inquiry, form, 'mice'))
            self.assertEqual(send.call_args_list[0].kwargs['recipient_list'], ['admin@example.com'])
            self.assertEqual(send.call_args_list[1].kwargs['recipient_list'], ['qa@example.com'])
            html = send.call_args_list[0].kwargs['html_message']
            self.assertIn('&lt;script&gt;', html)
            self.assertNotIn('<script>', html)

    @override_settings(
        TOURS_INQUIRY_EMAIL='safaris@example.com',
        HOTEL_INQUIRY_EMAIL='hotels@example.com',
        FLIGHT_INQUIRY_EMAIL='flights@example.com',
        TRANSFER_INQUIRY_EMAIL='operations@example.com',
        VISA_INQUIRY_EMAIL='visa@example.com',
        MICE_INQUIRY_EMAIL='corporate@example.com',
    )
    def test_each_service_routes_to_its_own_desk_with_custom_copy(self):
        expected = {
            'tours': ('safaris@example.com', 'Tours & Safaris'),
            'hotels': ('hotels@example.com', 'Hotel Booking'),
            'flights': ('flights@example.com', 'Flight Booking'),
            'transfers': ('operations@example.com', 'Ground Handling & Transfers'),
            'visa': ('visa@example.com', 'Visa & Travel Advisory'),
            'mice': ('corporate@example.com', 'Corporate Travel & MICE'),
        }
        inquiry = SimpleNamespace(pk=7, short_reference='ABC12345', contact_person='QA Client', email='qa@example.com', notes='Test')
        form = SimpleNamespace(fields={'notes': SimpleNamespace(label='Notes')})
        for service, (recipient, title) in expected.items():
            with self.subTest(service=service), patch('users.inquiry_email.send_email_via_mailtrap', return_value=True) as send:
                self.assertTrue(send_service_inquiry_emails(inquiry, form, service))
                self.assertEqual(send.call_args_list[0].kwargs['recipient_list'], [recipient])
                self.assertIn(title, send.call_args_list[0].kwargs['subject'])
                self.assertIn(conditional_escape(title), send.call_args_list[1].kwargs['html_message'])

    def test_https_timeout_and_provider_rejection_return_failure(self):
        for failure in [requests.Timeout(), requests.HTTPError()]:
            with self.subTest(failure=type(failure).__name__), patch('users.tasks.requests.post', side_effect=failure) as post:
                self.assertFalse(send_email_via_mailtrap('Test', '<p>Test</p>', 'info@example.com', ['qa@example.com']))
                self.assertEqual(post.call_args.kwargs['timeout'], (3, 8))

    def test_https_requires_explicit_provider_success(self):
        for accepted in [True, False]:
            with patch('users.tasks.requests.post') as post:
                post.return_value.json.return_value = {'success': accepted}
                self.assertEqual(send_email_via_mailtrap('Test', '<p>Test</p>', 'info@example.com', ['qa@example.com']), accepted)

    @override_settings(EMAIL_PROVIDER='resend', RESEND_API_KEY='test-resend-key')
    def test_resend_provider_uses_resend_api_and_requires_message_id(self):
        for response_body, accepted in [({'id': 'email_123'}, True), ({'error': 'Rejected'}, False)]:
            with self.subTest(response_body=response_body), patch('users.tasks.requests.post') as post:
                post.return_value.json.return_value = response_body
                self.assertEqual(
                    send_email_via_mailtrap('Test', '<p>Test</p>', 'Myriad <info@example.com>', ['qa@example.com']),
                    accepted,
                )
                self.assertEqual(post.call_args.args[0], 'https://api.resend.com/emails')
                self.assertEqual(post.call_args.kwargs['timeout'], (3, 8))
                self.assertEqual(post.call_args.kwargs['headers']['Authorization'], 'Bearer test-resend-key')
                self.assertEqual(post.call_args.kwargs['json']['from'], 'Myriad <info@example.com>')


from django.test import TestCase
from users.models import (
    FlightInquiry,
    HotelInquiry,
    MICEInquiry,
    NGOTravelInquiry,
    StudentTravelInquiry,
    TourSafariInquiry,
    TransferInquiry,
    VisaInquiry,
)


class ServiceInquiryPersistenceTests(TestCase):
    def test_public_forms_persist_valid_submission_when_mail_unavailable(self):
        common = {'contact_person': 'Website QA', 'email': 'qa@example.com', 'phone_number': '+254000000000'}
        cases = [
            ('/mice/', MICEInquiry, {'company_name': 'TEST', 'event_type': 'Meeting', 'attendees': 2, 'event_details': 'Test only'}),
            ('/student-travel/', StudentTravelInquiry, {'school_name': 'TEST', 'program_stage': 'Regional Round', 'number_of_students': 2, 'travel_details': 'Test only'}),
            ('/ngo-travel/', NGOTravelInquiry, {'organization_name': 'TEST', 'organization_type': 'NGO', 'travel_purpose': 'Field Operations', 'number_of_travelers': 2, 'travel_details': 'Test only'}),
        ]
        with patch('users.inquiry_email.send_service_inquiry_emails', return_value=False):
            for url, model, data in cases:
                with self.subTest(url=url):
                    response = self.client.post(url, {**common, **data})
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(model.objects.count(), 1)

    def test_each_about_service_has_a_dedicated_persisted_inquiry(self):
        common = {'contact_person': 'Website QA', 'email': 'service@example.com', 'phone_number': '+254700000000', 'preferred_contact': 'email'}
        cases = [
            ('/enquire/tours-safaris/', 'tours', TourSafariInquiry, {'destination': 'Maasai Mara', 'trip_style': 'wildlife', 'preferred_travel_dates': 'December 2026', 'adults': 2, 'children': 0, 'budget_currency': 'KES'}),
            ('/enquire/hotels/', 'hotels', HotelInquiry, {'destination': 'Diani', 'check_in': '2026-12-10', 'check_out': '2026-12-14', 'rooms': 1, 'adults': 2, 'children': 0, 'budget_currency': 'KES'}),
            ('/enquire/flights/', 'flights', FlightInquiry, {'trip_type': 'return', 'origin': 'Nairobi', 'destination': 'Dubai', 'departure_date': '2026-12-10', 'return_date': '2026-12-14', 'adults': 2, 'children': 0, 'infants': 0, 'cabin_class': 'economy'}),
            ('/enquire/transfers/', 'transfers', TransferInquiry, {'service_type': 'airport', 'pickup_location': 'JKIA', 'dropoff_location': 'Westlands', 'service_date': '2026-12-10', 'passengers': 2, 'luggage_count': 2}),
            ('/enquire/visa-advisory/', 'visa', VisaInquiry, {'applicant_nationality': 'Kenyan', 'destination_country': 'United Arab Emirates', 'intended_travel_date': '2026-12-10', 'visa_category': 'Tourist', 'number_of_applicants': 2, 'assistance_required': 'Document checklist'}),
            ('/mice/', 'mice', MICEInquiry, {'company_name': 'TEST', 'event_type': 'Meeting', 'attendees': 10, 'event_details': 'Test only', 'budget_currency': 'KES'}),
        ]
        with patch('users.antispam.check_form_submission', return_value=True), patch('users.inquiry_email.send_service_inquiry_emails', return_value=False):
            for url, service, model, data in cases:
                with self.subTest(url=url):
                    response = self.client.post(url, {**common, **data})
                    self.assertRedirects(response, f'/enquire/success/{service}/', fetch_redirect_response=False)
                    self.assertEqual(model.objects.count(), 1)

    def test_success_page_displays_reference_once_after_submission(self):
        data = {
            'contact_person': 'Reference QA', 'email': 'reference@example.com',
            'phone_number': '+254700000000', 'preferred_contact': 'email',
            'trip_type': 'one_way', 'origin': 'Nairobi', 'destination': 'Kigali',
            'departure_date': '2026-12-10', 'adults': 1, 'children': 0,
            'infants': 0, 'cabin_class': 'economy',
        }
        with patch('users.antispam.check_form_submission', return_value=True), patch(
            'users.inquiry_email.send_service_inquiry_emails', return_value=True
        ):
            response = self.client.post('/enquire/flights/', data)
        inquiry = FlightInquiry.objects.get()
        response = self.client.get(response['Location'])
        self.assertContains(response, inquiry.short_reference)
        self.assertContains(response, 'Keep this reference')

        response = self.client.get('/enquire/success/flights/')
        self.assertNotContains(response, inquiry.short_reference)

    def test_multi_city_flight_requires_additional_segments(self):
        data = {
            'contact_person': 'Multi City QA', 'email': 'multi@example.com',
            'phone_number': '+254700000000', 'preferred_contact': 'email',
            'trip_type': 'multi_city', 'origin': 'Nairobi', 'destination': 'Dubai',
            'departure_date': '2026-12-10', 'adults': 1, 'children': 0,
            'infants': 0, 'cabin_class': 'economy',
        }
        response = self.client.post('/enquire/flights/', data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'List the additional routes and preferred dates')
        self.assertFalse(FlightInquiry.objects.exists())

    def test_old_services_url_redirects_to_about_services(self):
        response = self.client.get('/services/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/aboutus/#our-services')

    def test_invalid_and_honeypot_submissions_create_no_service_record(self):
        self.assertEqual(self.client.post('/enquire/flights/', {'email': 'invalid'}).status_code, 200)
        self.assertEqual(FlightInquiry.objects.count(), 0)

        data = {
            'contact_person': 'Bot', 'email': 'bot@example.com', 'phone_number': '+254700000000',
            'trip_type': 'one_way', 'origin': 'Nairobi', 'destination': 'Dubai',
            'departure_date': '2026-12-10', 'adults': 1, 'children': 0, 'infants': 0,
            'cabin_class': 'economy', 'website': 'https://spam.example',
        }
        self.assertEqual(self.client.post('/enquire/flights/', data).status_code, 200)
        self.assertEqual(FlightInquiry.objects.count(), 0)

    def test_email_delivery_flags_are_recorded_without_losing_inquiry(self):
        data = {
            'contact_person': 'Email QA', 'email': 'email@example.com', 'phone_number': '+254700000000',
            'preferred_contact': 'email', 'destination': 'Diani', 'check_in': '2026-12-10',
            'check_out': '2026-12-14', 'rooms': 1, 'adults': 2, 'children': 0,
            'budget_currency': 'KES',
        }
        with patch('users.antispam.check_form_submission', return_value=True), patch('users.inquiry_email.send_email_via_mailtrap', side_effect=[True, False]):
            response = self.client.post('/enquire/hotels/', data)
        self.assertEqual(response.status_code, 302)
        inquiry = HotelInquiry.objects.get()
        self.assertTrue(inquiry.admin_notification_sent)
        self.assertFalse(inquiry.confirmation_email_sent)

    def test_admin_can_open_inquiry_and_start_prefilled_follow_up(self):
        admin_user = get_user_model().objects.create_superuser('service-admin', 'admin@example.com', 'password')
        inquiry = TourSafariInquiry.objects.create(
            contact_person='Safari Lead', email='lead@example.com', phone_number='+254700000000',
            destination='Maasai Mara', trip_style='wildlife', preferred_travel_dates='Flexible', adults=2,
        )
        self.client.force_login(admin_user)
        response = self.client.get(reverse('admin:users_toursafariinquiry_change', args=[inquiry.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create follow-up')
        self.assertContains(response, f'tour_inquiry={inquiry.pk}')

    def test_about_page_links_to_all_six_dedicated_forms(self):
        response = self.client.get('/aboutus/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['public_menus'])
        for route in ('tours_inquiry', 'hotel_inquiry', 'flight_inquiry', 'transfer_inquiry', 'visa_inquiry', 'micepage'):
            self.assertContains(response, reverse(f'users:{route}'))
        self.assertNotContains(response, 'href="/services/')
