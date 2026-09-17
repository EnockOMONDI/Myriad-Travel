
from django.contrib import admin
from django.urls import path, include, re_path
from . import views as tours_travels_views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from .health_check import (
    health_check, health_detailed, readiness_check,
    liveness_check, metrics, csp_report, version_info
)






urlpatterns = [
    path('admin/', admin.site.urls),
    path("ckeditor5/", include('django_ckeditor_5.urls')),  # CKEditor 5 file uploads

    # Health check endpoints
    path('health/', health_check, name='health_check'),
    path('health/detailed/', health_detailed, name='health_detailed'),
    path('health/ready/', readiness_check, name='readiness_check'),
    path('health/live/', liveness_check, name='liveness_check'),
    path('metrics/', metrics, name='metrics'),
    path('csp-report/', csp_report, name='csp_report'),
    path('version/', version_info, name='version_info'),

    # Favicon handling
    path('favicon.ico', RedirectView.as_view(url='/static/assets/images/favicon_io/favicon.ico', permanent=True)),

    # Font testing (development only)
    path('font-test/', tours_travels_views.font_test, name='font_test'),

    #path('',tours_travels_views.home,name = 'home'),

    path('', include(('users.urls', 'users'), namespace='home')),
    path('adminside/', include(('adminside.urls', 'adminside'), namespace='adminside')),
    path('blog/', include(('blog.urls', 'blog'), namespace='blog')),
    path('login/',auth_views.LoginView.as_view(template_name='users/login.html'),name='login'),
    path('logout/',auth_views.LogoutView.as_view(template_name='users/index.html'),name='logout'),
    path('mail/',tours_travels_views.mail,name='mail'),
    path('system-status/', include(('status.urls', 'status'), namespace='system-status')),

    path('', include('users.urls')),


]

# Serve media files in development
if settings.DEBUG == True:
    # static function below returns a list of url patterns of static path
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers for production
handler400 = 'tours_travels.views.custom_400_view'
handler403 = 'tours_travels.views.custom_403_view'
handler404 = 'tours_travels.views.custom_404_view'
handler500 = 'tours_travels.views.custom_500_view'