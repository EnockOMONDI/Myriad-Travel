from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from adminside.models import Destination, Package
from users.models import TripFeedback


class TripFeedbackTests(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(
            name="Amboseli",
            slug="amboseli",
            destination_type=Destination.PLACE,
            description="Amboseli National Park",
            is_active=True,
        )
        self.package = Package.objects.create(
            name="Amboseli Safari",
            slug="amboseli-safari",
            description="Safari below Kilimanjaro.",
            main_destination=self.destination,
            duration_days=3,
            duration_nights=2,
            adult_price=44500,
            child_price=30000,
            inclusions="Transport",
            exclusions="Personal expenses",
            status=Package.PUBLISHED,
        )

    def test_private_feedback_link_renders(self):
        feedback = TripFeedback.objects.create(
            client_name="Jane Client",
            client_email="jane@example.com",
            package=self.package,
            destination_or_trip="Amboseli Safari",
        )

        response = self.client.get(reverse("users:trip_feedback", kwargs={"token": feedback.token}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Private Client Feedback")
        self.assertContains(response, "Amboseli Safari")

    def test_client_can_submit_trip_feedback(self):
        feedback = TripFeedback.objects.create(
            client_name="Jane Client",
            client_email="jane@example.com",
            package=self.package,
            destination_or_trip="Amboseli Safari",
        )

        response = self.client.post(reverse("users:trip_feedback", kwargs={"token": feedback.token}), {
            "client_name": "Jane Client",
            "client_email": "jane@example.com",
            "rating": 5,
            "feedback": "Excellent trip coordination.",
            "highlights": "The guide and itinerary were wonderful.",
            "improvements": "Nothing major.",
            "permission_to_publish": "on",
        })

        feedback.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(feedback.status, TripFeedback.SUBMITTED)
        self.assertEqual(feedback.rating, 5)
        self.assertTrue(feedback.permission_to_publish)
        self.assertIsNotNone(feedback.submitted_at)

    def test_only_visible_approved_feedback_reaches_public_context(self):
        visible = TripFeedback.objects.create(
            client_name="Visible Client",
            package=self.package,
            rating=5,
            feedback="Public review.",
            permission_to_publish=True,
            is_visible_on_site=True,
            status=TripFeedback.SUBMITTED,
        )
        TripFeedback.objects.create(
            client_name="Hidden Client",
            package=self.package,
            rating=5,
            feedback="Hidden review.",
            permission_to_publish=True,
            is_visible_on_site=False,
            status=TripFeedback.SUBMITTED,
        )

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, visible.client_name)
        self.assertNotContains(response, "Hidden Client")
