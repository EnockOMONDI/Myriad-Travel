from django.urls import path
from . import views

app_name = 'adminside'

urlpatterns = [
    # Destination URLs
    path('destinations/', views.destination_list, name='destination_list'),
    path('destinations/<slug:slug>/', views.destination_detail, name='destination_detail'),

    # Package URLs
    path('packages/', views.package_list, name='package_list'),
    path('packages/<slug:slug>/', views.package_detail, name='package_detail'),
    path('user-packages/', views.user_package_list, name='user_package_list'),

    # Accommodation URLs
    path('accommodations/', views.accommodation_list, name='accommodation_list'),
    path('accommodations/<slug:slug>/', views.accommodation_detail, name='accommodation_detail'),

    # Travel Mode URLs
    path('travel-options/', views.travel_mode_list, name='travel_mode_list'),

    # AJAX URLs for dynamic filtering
    path('ajax/destinations/', views.get_destinations_ajax, name='get_destinations_ajax'),
    path('ajax/packages/', views.get_packages_by_destination_ajax, name='get_packages_by_destination_ajax'),
    path('ajax/accommodations/', views.get_accommodations_by_destination_ajax, name='get_accommodations_by_destination_ajax'),
]
