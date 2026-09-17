from types import SimpleNamespace
from unittest.mock import Mock, patch
import requests
from django.test import SimpleTestCase, RequestFactory, override_settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages import get_messages
from users import views
from users.tasks import send_email_via_mailtrap
from users.inquiry_email import send_service_inquiry_emails


@override_settings(DEFAULT_FROM_EMAIL='Mbugani <info@example.com>', ADMIN_EMAIL='admin@example.com', MAILTRAP_API_TOKEN='test-token')
class ServiceInquiryTests(SimpleTestCase):
    def request(self):
        request = RequestFactory().post('/mice/', {})
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_all_three_forms_save_once_and_redirect_after_mail_failure(self):
        for view, form_name in [(views.micepage, 'MICEInquiryForm'), (views.student_travel, 'StudentTravelInquiryForm'), (views.ngo_travel, 'NGOTravelInquiryForm')]:
            with self.subTest(form=form_name), patch('users.views.' + form_name) as form_class, patch('users.inquiry_email.send_service_inquiry_emails', return_value=False):
                form = form_class.return_value
                form.is_valid.return_value = True
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
        with patch('users.views.MICEInquiryForm'), patch('users.inquiry_email.send_service_inquiry_emails', return_value=True):
            request = self.request()
            response = views.micepage(request)
            self.assertEqual(response.status_code, 302)
            self.assertIn('successfully', str(list(get_messages(request))[0]))

    def test_notifications_route_to_admin_and_customer_and_escape_input(self):
        inquiry = SimpleNamespace(pk=42, contact_person='QA', email='qa@example.com', event_details='<script>alert(1)</script>')
        form = SimpleNamespace(fields={'event_details': SimpleNamespace(label='Details')})
        with patch('users.inquiry_email.send_email_via_mailtrap', return_value=True) as send:
            self.assertTrue(send_service_inquiry_emails(inquiry, form, 'MICE'))
            self.assertEqual(send.call_args_list[0].kwargs['recipient_list'], ['admin@example.com'])
            self.assertEqual(send.call_args_list[1].kwargs['recipient_list'], ['qa@example.com'])
            html = send.call_args_list[0].kwargs['html_message']
            self.assertIn('&lt;script&gt;', html)
            self.assertNotIn('<script>', html)

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


from django.test import TestCase
from users.models import MICEInquiry, StudentTravelInquiry, NGOTravelInquiry


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
