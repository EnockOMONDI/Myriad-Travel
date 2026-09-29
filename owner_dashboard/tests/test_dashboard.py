from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from adminside.models import Destination, Package
from blog.models import Post
from users.models import Booking, FollowUp, QuoteRequest, TripFeedback


class OwnerDashboardTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="password123",
            is_staff=True,
        )
        self.customer = User.objects.create_user(
            username="customer",
            email="customer@example.com",
            password="password123",
        )
        self.destination = Destination.objects.create(
            name="Chalbi Desert",
            slug="chalbi-desert",
            destination_type=Destination.PLACE,
            description="Northern Kenya desert experience.",
            is_active=True,
        )
        self.package = Package.objects.create(
            name="Twende Chalbi",
            slug="twende-chalbi",
            description="Explore Kenya's spectacular north.",
            main_destination=self.destination,
            duration_days=5,
            duration_nights=4,
            adult_price=58000,
            child_price=45000,
            inclusions="Transport and accommodation.",
            exclusions="Personal expenses.",
            status=Package.PUBLISHED,
        )

    def test_dashboard_requires_staff_login(self):
        response = self.client.get(reverse("owner_dashboard:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_dashboard_renders_for_staff(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse("owner_dashboard:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Myriad Travel Dashboard")
        self.assertContains(response, "Business Overview")
        self.assertContains(response, "Open follow-ups")

    def test_dashboard_metrics_include_current_business_records(self):
        Booking.objects.create(
            booking_reference="NVT1234567",
            package=self.package,
            user=self.customer,
            full_name="Jane Client",
            email="jane@example.com",
            phone_number="0712345678",
            package_price=58000,
            total_amount=58000,
            status=Booking.PENDING,
        )
        QuoteRequest.objects.create(
            full_name="Brian Lead",
            email="brian@example.com",
            phone_number="0711222333",
            destination="Diani",
            preferred_travel_dates="Flexible",
            number_of_travelers=2,
            status="new",
        )
        Post.objects.create(
            user=self.staff,
            title="Chalbi Travel Guide",
            content="Travel guide content.",
            status="published",
        )
        FollowUp.objects.create(
            title="Call Brian Lead",
            follow_up_type=FollowUp.QUOTE,
            due_at=timezone.now(),
            assigned_to=self.staff,
            customer_name="Brian Lead",
        )
        TripFeedback.objects.create(
            client_name="Jane Client",
            package=self.package,
            rating=5,
            feedback="Wonderful trip.",
            permission_to_publish=True,
            status=TripFeedback.SUBMITTED,
        )
        self.client.force_login(self.staff)

        response = self.client.get(reverse("owner_dashboard:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pending bookings")
        self.assertContains(response, "Published blogs")
        self.assertContains(response, "New quotes")
        self.assertContains(response, "Call Brian Lead")
        self.assertContains(response, "Trip feedback")
        self.assertContains(response, "Jane Client")
