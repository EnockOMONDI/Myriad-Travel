"""
Health check views for production monitoring
"""

import json
import time
import sys
import os
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import User
from adminside.models import Package, Destination
from users.models import Booking


@require_http_methods(["GET"])
def health_check(request):
    """
    Basic health check endpoint for load balancers
    Returns 200 OK if the application is running
    """
    return HttpResponse("OK", content_type="text/plain", status=200)


@require_http_methods(["GET"])
def health_detailed(request):
    """
    Detailed health check with database and cache status
    """
    start_time = time.time()
    health_data = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": getattr(settings, 'VERSION', '1.0.0'),
        "environment": "production" if not settings.DEBUG else "development",
        "checks": {}
    }
    
    # Database health check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_data["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_data["status"] = "unhealthy"
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
    
    # Cache health check
    try:
        cache_key = "health_check_test"
        cache_value = "test_value"
        cache.set(cache_key, cache_value, 30)
        retrieved_value = cache.get(cache_key)
        
        if retrieved_value == cache_value:
            health_data["checks"]["cache"] = {
                "status": "healthy",
                "message": "Cache is working"
            }
        else:
            health_data["checks"]["cache"] = {
                "status": "unhealthy",
                "message": "Cache read/write test failed"
            }
    except Exception as e:
        health_data["checks"]["cache"] = {
            "status": "unhealthy",
            "message": f"Cache error: {str(e)}"
        }
    
    # Model health checks
    try:
        user_count = User.objects.count()
        package_count = Package.objects.count()
        destination_count = Destination.objects.count()
        booking_count = Booking.objects.count()
        
        health_data["checks"]["models"] = {
            "status": "healthy",
            "message": "All models accessible",
            "counts": {
                "users": user_count,
                "packages": package_count,
                "destinations": destination_count,
                "bookings": booking_count
            }
        }
    except Exception as e:
        health_data["status"] = "unhealthy"
        health_data["checks"]["models"] = {
            "status": "unhealthy",
            "message": f"Model access failed: {str(e)}"
        }
    
    # Email configuration check
    try:
        from django.core.mail import get_connection
        connection = get_connection()
        # Don't actually send email, just check configuration
        health_data["checks"]["email"] = {
            "status": "healthy",
            "message": "Email backend configured",
            "backend": settings.EMAIL_BACKEND
        }
    except Exception as e:
        health_data["checks"]["email"] = {
            "status": "warning",
            "message": f"Email configuration issue: {str(e)}"
        }
    
    # Static files check
    try:
        import os
        static_root = getattr(settings, 'STATIC_ROOT', None)
        if static_root and os.path.exists(static_root):
            health_data["checks"]["static_files"] = {
                "status": "healthy",
                "message": "Static files directory exists",
                "path": static_root
            }
        else:
            health_data["checks"]["static_files"] = {
                "status": "warning",
                "message": "Static files directory not found or not configured"
            }
    except Exception as e:
        health_data["checks"]["static_files"] = {
            "status": "warning",
            "message": f"Static files check failed: {str(e)}"
        }
    
    # Response time
    end_time = time.time()
    health_data["response_time_ms"] = round((end_time - start_time) * 1000, 2)
    
    # Overall status
    if any(check["status"] == "unhealthy" for check in health_data["checks"].values()):
        health_data["status"] = "unhealthy"
        status_code = 503
    elif any(check["status"] == "warning" for check in health_data["checks"].values()):
        health_data["status"] = "degraded"
        status_code = 200
    else:
        status_code = 200
    
    return JsonResponse(health_data, status=status_code)


@require_http_methods(["GET"])
def readiness_check(request):
    """
    Readiness check for Kubernetes/container orchestration
    Returns 200 when the application is ready to serve traffic
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        # Check that essential models are accessible
        Package.objects.exists()
        Destination.objects.exists()
        
        return JsonResponse({
            "status": "ready",
            "timestamp": time.time()
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            "status": "not_ready",
            "error": str(e),
            "timestamp": time.time()
        }, status=503)


@require_http_methods(["GET"])
def liveness_check(request):
    """
    Liveness check for Kubernetes/container orchestration
    Returns 200 if the application process is alive
    """
    return JsonResponse({
        "status": "alive",
        "timestamp": time.time(),
        "pid": os.getpid() if hasattr(os, 'getpid') else None
    }, status=200)


@require_http_methods(["GET"])
def metrics(request):
    """
    Basic metrics endpoint for monitoring
    """
    try:
        metrics_data = {
            "timestamp": time.time(),
            "database": {
                "users_count": User.objects.count(),
                "packages_count": Package.objects.count(),
                "destinations_count": Destination.objects.count(),
                "bookings_count": Booking.objects.count(),
                "published_packages": Package.objects.filter(status=Package.PUBLISHED).count(),
                "pending_bookings": Booking.objects.filter(status='pending').count(),
                "confirmed_bookings": Booking.objects.filter(status='confirmed').count(),
            },
            "system": {
                "debug_mode": settings.DEBUG,
                "allowed_hosts": settings.ALLOWED_HOSTS,
                "database_engine": settings.DATABASES['default']['ENGINE'],
                "cache_backend": settings.CACHES['default']['BACKEND'],
                "email_backend": settings.EMAIL_BACKEND,
            }
        }
        
        # Add memory usage if available
        try:
            import psutil
            process = psutil.Process()
            metrics_data["system"]["memory_usage_mb"] = round(
                process.memory_info().rss / 1024 / 1024, 2
            )
            metrics_data["system"]["cpu_percent"] = process.cpu_percent()
        except ImportError:
            pass
        
        return JsonResponse(metrics_data, status=200)
        
    except Exception as e:
        return JsonResponse({
            "error": "Failed to collect metrics",
            "message": str(e),
            "timestamp": time.time()
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def csp_report(request):
    """
    Content Security Policy violation report endpoint
    """
    try:
        if request.content_type == 'application/csp-report':
            report_data = json.loads(request.body.decode('utf-8'))
            
            # Log CSP violation (in production, you might want to send to monitoring service)
            import logging
            logger = logging.getLogger('django.security')
            logger.warning(f"CSP Violation: {report_data}")
            
            return HttpResponse("OK", status=200)
        else:
            return HttpResponse("Invalid content type", status=400)
            
    except Exception as e:
        return HttpResponse(f"Error processing CSP report: {str(e)}", status=500)


@require_http_methods(["GET"])
def version_info(request):
    """
    Version and build information endpoint
    """
    import os
    import django
    
    version_data = {
        "application": {
            "name": "Mbugani Luxe Adventures",
            "version": getattr(settings, 'VERSION', '1.0.0'),
            "build_number": getattr(settings, 'BUILD_NUMBER', 'unknown'),
            "commit_hash": getattr(settings, 'COMMIT_HASH', 'unknown'),
            "deployment_date": getattr(settings, 'DEPLOYMENT_DATE', 'unknown'),
        },
        "framework": {
            "django_version": django.get_version(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        },
        "environment": {
            "debug": settings.DEBUG,
            "environment": "production" if not settings.DEBUG else "development",
            "time_zone": settings.TIME_ZONE,
            "language_code": settings.LANGUAGE_CODE,
        },
        "timestamp": time.time()
    }
    
    return JsonResponse(version_data, status=200)
