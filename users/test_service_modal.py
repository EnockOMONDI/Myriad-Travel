from django.test import TestCase
from django.urls import reverse
from django.utils.html import conditional_escape


class ServiceInquiryModalTests(TestCase):
    service_titles = {
        'tours': 'Plan a Tour or Safari',
        'hotels': 'Request a Hotel Stay',
        'flights': 'Request Flight Options',
        'transfers': 'Arrange Ground Transport',
        'visa': 'Request Visa & Travel Advice',
        'mice': 'Plan Corporate Travel or an Event',
    }

    def test_each_service_modal_loads_the_existing_service_form(self):
        for service, title in self.service_titles.items():
            with self.subTest(service=service):
                response = self.client.get(
                    reverse('users:service_inquiry_modal', kwargs={'service': service}),
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'data-service-inquiry-form')
                self.assertContains(response, conditional_escape(title))

    def test_unknown_service_is_not_exposed_as_a_modal(self):
        response = self.client.get('/enquire/modal/not-a-service/')
        self.assertEqual(response.status_code, 404)

    def test_invalid_modal_submission_returns_the_same_form_for_correction(self):
        for service in self.service_titles:
            with self.subTest(service=service):
                response = self.client.post(
                    reverse('users:service_inquiry_modal', kwargs={'service': service}),
                    {'email': 'not-an-email'},
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'data-service-inquiry-form')
