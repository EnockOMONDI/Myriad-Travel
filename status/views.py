from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
from django.core.mail import get_connection
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth.models import User
from adminside.models import Destination, Package, Accommodation
from blog.models import Post
from users.models import Booking
import smtplib
import os


def system_status(request):
    """
    System status dashboard showing database statistics and system health
    """
    try:
        # Content Statistics
        content_stats = get_content_statistics()

        # Recent Activity
        recent_activity = get_recent_activity()

        # System Health
        system_health = get_system_health()

        context = {
            'content_stats': content_stats,
            'recent_activity': recent_activity,
            'system_health': system_health,
            'last_updated': timezone.now(),
            'page_title': 'System Status Dashboard'
        }

        return render(request, 'status/dashboard.html', context)

    except Exception as e:
        # Error handling for database connection issues
        context = {
            'error': str(e),
            'page_title': 'System Status - Error',
            'last_updated': timezone.now(),
        }
        return render(request, 'status/dashboard.html', context)


def get_content_statistics():
    """
    Gather content statistics from the database
    """
    try:
        # Destination statistics by type
        destinations = {
            'countries': Destination.objects.filter(
                destination_type=Destination.COUNTRY,
                is_active=True
            ).count(),
            'cities': Destination.objects.filter(
                destination_type=Destination.CITY,
                is_active=True
            ).count(),
            'places': Destination.objects.filter(
                destination_type=Destination.PLACE,
                is_active=True
            ).count(),
            'total': Destination.objects.filter(is_active=True).count()
        }

        # Package statistics by status
        packages = {
            'published': Package.objects.filter(status=Package.PUBLISHED).count(),
            'draft': Package.objects.filter(status=Package.DRAFT).count(),
            'archived': Package.objects.filter(status=Package.ARCHIVED).count(),
            'total': Package.objects.all().count()
        }

        # Accommodation statistics
        accommodations = {
            'active': Accommodation.objects.filter(is_active=True).count(),
            'inactive': Accommodation.objects.filter(is_active=False).count(),
            'total': Accommodation.objects.all().count()
        }

        # Blog post statistics
        blog_posts = {
            'published': Post.objects.filter(status='published').count(),
            'draft': Post.objects.filter(status='draft').count(),
            'total': Post.objects.all().count()
        }

        # Booking statistics
        bookings = {
            'confirmed': Booking.objects.filter(status='confirmed').count(),
            'pending': Booking.objects.filter(status='pending').count(),
            'cancelled': Booking.objects.filter(status='cancelled').count(),
            'total': Booking.objects.all().count()
        }

        # User statistics
        users = {
            'total': User.objects.all().count(),
            'active': User.objects.filter(is_active=True).count(),
            'staff': User.objects.filter(is_staff=True).count(),
            'superusers': User.objects.filter(is_superuser=True).count()
        }

        return {
            'destinations': destinations,
            'packages': packages,
            'accommodations': accommodations,
            'blog_posts': blog_posts,
            'bookings': bookings,
            'users': users
        }

    except Exception as e:
        return {'error': str(e)}


def get_recent_activity():
    """
    Get recent activity from various models
    """
    try:
        # Latest destinations
        latest_destinations = Destination.objects.filter(
            is_active=True
        ).order_by('-created_at')[:5].values(
            'name', 'destination_type', 'created_at', 'slug'
        )

        # Latest packages
        latest_packages = Package.objects.all().order_by('-created_at')[:5].values(
            'name', 'status', 'created_at', 'slug'
        )

        # Latest user registrations
        latest_users = User.objects.all().order_by('-date_joined')[:5].values(
            'username', 'email', 'date_joined', 'is_active'
        )

        # Latest bookings
        latest_bookings = Booking.objects.all().order_by('-created_at')[:5].values(
            'full_name', 'status', 'created_at', 'total_amount'
        )

        return {
            'destinations': list(latest_destinations),
            'packages': list(latest_packages),
            'users': list(latest_users),
            'bookings': list(latest_bookings)
        }

    except Exception as e:
        return {'error': str(e)}


def get_system_health():
    """
    Check system health metrics
    """
    health_status = {
        'database': check_database_connection(),
        'email': check_email_system(),
        'database_size': get_database_size()
    }

    return health_status


def check_database_connection():
    """
    Test database connection
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return {
                'status': 'healthy',
                'message': 'Database connection successful',
                'timestamp': timezone.now()
            }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Database connection failed: {str(e)}',
            'timestamp': timezone.now()
        }


def check_email_system():
    """
    Test email system connectivity
    """
    try:
        # Test SMTP connection
        connection = get_connection()
        connection.open()
        connection.close()

        return {
            'status': 'healthy',
            'message': 'Email system operational',
            'smtp_host': settings.EMAIL_HOST,
            'timestamp': timezone.now()
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Email system error: {str(e)}',
            'timestamp': timezone.now()
        }


def get_database_size():
    """
    Get database size information (SQLite specific)
    """
    try:
        db_path = settings.DATABASES['default']['NAME']
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            size_mb = round(size_bytes / (1024 * 1024), 2)
            return {
                'size_mb': size_mb,
                'size_bytes': size_bytes,
                'path': db_path
            }
        else:
            return {
                'size_mb': 0,
                'size_bytes': 0,
                'path': 'Database file not found'
            }
    except Exception as e:
        return {
            'error': str(e)
        }
