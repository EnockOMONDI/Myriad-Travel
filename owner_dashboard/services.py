from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.urls import reverse
from django.utils import timezone

from adminside.models import Destination, HeroSlider, Itinerary, Package
from blog.models import Post
from users.models import (
    Booking,
    FollowUp,
    JobApplication,
    JobListing,
    MICEInquiry,
    NGOTravelInquiry,
    NewsletterSubscription,
    QuoteRequest,
    StudentTravelInquiry,
    TripFeedback,
    UserBookings,
)


def build_dashboard_context(user):
    today = timezone.now().date()
    total_booking_value = sum_booking_amounts(Booking.objects.all())
    pending_booking_value = sum_booking_amounts(Booking.objects.filter(status=Booking.PENDING))
    confirmed_booking_value = sum_booking_amounts(Booking.objects.filter(status=Booking.CONFIRMED))

    metrics = [
        metric("Total bookings", Booking.objects.count() + UserBookings.objects.count(), "All booking records"),
        metric("Pending bookings", Booking.objects.filter(status=Booking.PENDING).count(), "Awaiting confirmation"),
        metric("Confirmed bookings", Booking.objects.filter(status=Booking.CONFIRMED).count(), "Ready for operations"),
        metric("Booking value", money(total_booking_value), "Current recorded value"),
        metric("Published packages", Package.objects.filter(status=Package.PUBLISHED).count(), "Visible package catalog"),
        metric("Published blogs", Post.objects.filter(status="published").count(), "Live travel content"),
        metric("New quotes", QuoteRequest.objects.filter(status="new").count(), "Needs sales follow-up"),
        metric("Open follow-ups", FollowUp.objects.open().count(), "Team workload"),
        metric("Trip feedback", TripFeedback.objects.filter(status=TripFeedback.SUBMITTED).count(), "Awaiting admin review"),
    ]

    finance = {
        "total_booking_value": money(total_booking_value),
        "pending_booking_value": money(pending_booking_value),
        "confirmed_booking_value": money(confirmed_booking_value),
        "paid_legacy_bookings": UserBookings.objects.filter(paid=True).count(),
        "unpaid_legacy_bookings": UserBookings.objects.filter(paid=False).count(),
    }

    needs_attention = [
        attention(
            "Pending bookings",
            Booking.objects.filter(status=Booking.PENDING).count(),
            "Bookings waiting for team confirmation.",
            admin_url("users_booking_changelist") + "?status__exact=pending",
        ),
        attention(
            "New quote requests",
            QuoteRequest.objects.filter(status="new").count(),
            "Fresh quote leads that should be contacted.",
            admin_url("users_quoterequest_changelist") + "?status__exact=new",
        ),
        attention(
            "Overdue follow-ups",
            FollowUp.objects.overdue().count(),
            "Follow-ups past their due date.",
            admin_url("users_followup_changelist") + "?status__in=pending,in_progress",
            urgent=True,
        ),
        attention(
            "Published packages missing images",
            Package.objects.filter(status=Package.PUBLISHED).filter(
                Q(featured_image__isnull=True) | Q(featured_image="")
            ).count(),
            "Upload a package image to replace the destination default on its selling page.",
            admin_url("adminside_package_changelist") + "?status__exact=published&image_status=missing",
        ),
        attention(
            "Packages missing itinerary",
            Package.objects.exclude(id__in=Itinerary.objects.values("package_id")).count(),
            "Package pages are stronger with day-by-day plans.",
            admin_url("adminside_package_changelist"),
        ),
        attention(
            "Draft packages",
            Package.objects.filter(status=Package.DRAFT).count(),
            "Unpublished package records.",
            admin_url("adminside_package_changelist") + "?status__exact=draft",
        ),
        attention(
            "Unconfirmed subscribers",
            NewsletterSubscription.objects.filter(is_active=True, is_confirmed=False).count(),
            "Newsletter subscribers awaiting confirmation.",
            admin_url("users_newslettersubscription_changelist") + "?is_confirmed__exact=0",
        ),
        attention(
            "Trip feedback to review",
            TripFeedback.objects.filter(status=TripFeedback.SUBMITTED).count(),
            "Client feedback submitted through private trip links.",
            admin_url("users_tripfeedback_changelist") + "?status__exact=submitted",
        ),
    ]

    quick_actions = [
        action_group("Sales", [
            action("Bookings", admin_url("users_booking_changelist")),
            action("Quote requests", admin_url("users_quoterequest_changelist")),
            action("Follow-ups", admin_url("users_followup_changelist")),
            action("MICE inquiries", admin_url("users_miceinquiry_changelist")),
        ]),
        action_group("Catalog / Packages", [
            action("Add package", admin_url("adminside_package_add")),
            action("Manage packages", admin_url("adminside_package_changelist")),
            action("Destinations", admin_url("adminside_destination_changelist")),
            action("Itineraries", admin_url("adminside_itinerary_changelist")),
        ]),
        action_group("Operations", [
            action("Student travel", admin_url("users_studenttravelinquiry_changelist")),
            action("NGO travel", admin_url("users_ngotravelinquiry_changelist")),
            action("Accommodations", admin_url("adminside_accommodation_changelist")),
            action("Travel modes", admin_url("adminside_travelmode_changelist")),
        ]),
        action_group("Content", [
            action("Blog posts", admin_url("blog_post_changelist")),
            action("Trip feedback", admin_url("users_tripfeedback_changelist")),
            action("Hero slider", admin_url("adminside_heroslider_changelist")),
            action("Newsletter", admin_url("users_newslettersubscription_changelist")),
            action("Jobs", admin_url("users_joblisting_changelist")),
        ]),
        action_group("Access Control", [
            action("Users", admin_url("auth_user_changelist")),
            action("Groups", admin_url("auth_group_changelist")),
            action("Django admin", reverse("admin:index")),
        ]),
    ]

    recent_activity = {
        "bookings": Booking.objects.select_related("package").order_by("-created_at")[:6],
        "quotes": QuoteRequest.objects.select_related("package").order_by("-created_at")[:6],
        "followups": FollowUp.objects.select_related("assigned_to", "booking", "quote_request").order_by("-updated_at")[:6],
        "feedback": TripFeedback.objects.select_related("package").order_by("-updated_at")[:6],
        "inquiries": recent_inquiries(),
    }

    operations = {
        "upcoming_bookings": Booking.objects.filter(travel_date__gte=today).exclude(status=Booking.CANCELLED).order_by("travel_date")[:8],
        "open_followups": FollowUp.objects.open().order_by("due_at", "-priority")[:8],
        "job_applications": JobApplication.objects.order_by("-created_at")[:5],
    }

    catalog = {
        "total_destinations": Destination.objects.count(),
        "active_hero_slides": HeroSlider.objects.filter(is_active=True).count(),
        "active_jobs": JobListing.objects.filter(is_active=True).count(),
        "draft_blogs": Post.objects.filter(status="draft").count(),
    }

    return {
        "page_title": "Owner Dashboard",
        "metrics": metrics,
        "finance": finance,
        "needs_attention": [item for item in needs_attention if item["count"]],
        "quick_actions": quick_actions,
        "recent_activity": recent_activity,
        "operations": operations,
        "catalog": catalog,
    }


def metric(label, value, helper):
    return {"label": label, "value": value, "helper": helper}


def attention(title, count, description, url, urgent=False):
    return {
        "title": title,
        "count": count,
        "description": description,
        "url": url,
        "urgent": urgent,
    }


def action_group(title, actions):
    return {"title": title, "actions": actions}


def action(label, url):
    return {"label": label, "url": url}


def admin_url(name):
    return reverse(f"admin:{name}")


def money(value):
    amount = value or Decimal("0")
    return f"KSh {amount:,.0f}"


def sum_booking_amounts(queryset):
    return queryset.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")


def recent_inquiries():
    items = []
    for inquiry in MICEInquiry.objects.order_by("-created_at")[:3]:
        items.append({"kind": "MICE", "name": inquiry.company_name, "created_at": inquiry.created_at})
    for inquiry in StudentTravelInquiry.objects.order_by("-created_at")[:3]:
        items.append({"kind": "Student", "name": inquiry.school_name, "created_at": inquiry.created_at})
    for inquiry in NGOTravelInquiry.objects.order_by("-created_at")[:3]:
        items.append({"kind": "NGO", "name": inquiry.organization_name, "created_at": inquiry.created_at})
    return sorted(items, key=lambda item: item["created_at"], reverse=True)[:6]
