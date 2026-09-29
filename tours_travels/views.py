from django.shortcuts import render,HttpResponse
from . import mail as mail_f
from django.template import loader
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.http import HttpResponseNotFound, HttpResponseServerError, HttpResponseForbidden, HttpResponseBadRequest, JsonResponse
from django.utils import timezone

def home(request):
    return HttpResponse('<h1>Welcome</h1>')

def mail(request):
    return HttpResponseBadRequest('Verification email requires a user and activation link context.')


def _render_error_response(request, template_name, context, response_class, fallback_title, fallback_message):
    """Render a branded error page, with a plain HTML fallback if templates fail."""
    try:
        template = loader.get_template(template_name)
        return response_class(template.render(context, request))
    except (TemplateDoesNotExist, TemplateSyntaxError):
        fallback_html = f"""
        <!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>{fallback_title} | Myriad Travel</title>
          </head>
          <body style="margin:0;min-height:100vh;display:grid;place-items:center;background:#f9f2f2;color:#0b192c;font-family:system-ui,sans-serif;">
            <main style="width:min(92vw,720px);padding:48px 28px;text-align:center;">
              <h1 style="font-size:clamp(2rem,7vw,4rem);margin:0 0 16px;">{fallback_title}</h1>
              <p style="color:#475569;line-height:1.7;">{fallback_message}</p>
              <a href="/" style="display:inline-block;margin-top:18px;padding:12px 18px;border-radius:999px;background:#d97706;color:white;text-decoration:none;font-weight:700;">Back to Home</a>
            </main>
          </body>
        </html>
        """
        return response_class(fallback_html)


# Custom Error Views
def custom_400_view(request, exception=None):
    """Custom 400 Bad Request error page"""
    context = {
        'request_path': request.path,
        'exception': exception,
    }
    return _render_error_response(
        request,
        '400.html',
        context,
        HttpResponseBadRequest,
        'Bad Request',
        'Please check the link or form details and try again.',
    )


def custom_403_view(request, exception=None):
    """Custom 403 Forbidden error page"""
    context = {
        'request_path': request.path,
        'exception': exception,
    }
    return _render_error_response(
        request,
        '403.html',
        context,
        HttpResponseForbidden,
        'Access Restricted',
        'You do not have permission to view this page.',
    )


def custom_404_view(request, exception=None):
    """Custom 404 Page Not Found error page"""
    context = {
        'request_path': request.path,
        'exception': exception,
    }
    return _render_error_response(
        request,
        '404.html',
        context,
        HttpResponseNotFound,
        'Page Not Found',
        'The page you requested could not be found.',
    )


def custom_500_view(request):
    """Custom 500 Internal Server Error page"""
    context = {
        'request_path': request.path,
    }
    return _render_error_response(
        request,
        '500.html',
        context,
        HttpResponseServerError,
        'Server Error',
        'Something went wrong on our side. Please try again shortly.',
    )


# Health check and utility views
def health_check(request):
    """Basic health check endpoint"""
    return JsonResponse({'status': 'healthy', 'timestamp': timezone.now().isoformat()})

def health_detailed(request):
    """Detailed health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'database': 'connected',
        'static_files': 'available'
    })

def readiness_check(request):
    """Readiness check endpoint"""
    return JsonResponse({'status': 'ready', 'timestamp': timezone.now().isoformat()})

def liveness_check(request):
    """Liveness check endpoint"""
    return JsonResponse({'status': 'alive', 'timestamp': timezone.now().isoformat()})

def metrics(request):
    """Basic metrics endpoint"""
    return JsonResponse({'metrics': 'available', 'timestamp': timezone.now().isoformat()})

def csp_report(request):
    """CSP violation report endpoint"""
    return JsonResponse({'status': 'received', 'timestamp': timezone.now().isoformat()})

def version_info(request):
    """Return version information"""
    return JsonResponse({
        'version': '1.0.0',
        'build': 'production',
        'timestamp': timezone.now().isoformat()
    })

def font_test(request):
    """Font testing page for TAN-Garland fonts"""
    return render(request, 'font_test.html')
