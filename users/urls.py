from django.urls import path,include
from . import views
from . import checkout_views

app_name = 'users'

urlpatterns = [
    path('', views.home, name='users-home'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('services/', views.services, name='services'),
    path('corporate/', views.corporate, name='corporatepage'),
    path('holidays/', views.holidays, name='holidayspage'),
    path('mice/', views.micepage, name='micepage'),
    path('student-travel/', views.student_travel, name='student-travel'),
    path('ngo-travel/', views.ngo_travel, name='ngo-travel'),
    path('contactus/', views.contactus, name='contactus'),
    path('register/',views.register,name='users-register'),
    path('success/', views.success, name='success'),
    path('destination/<int:id>/',views.destination,name='users-destination'),
    path('search/',views.search, name="search"),

    path('bookings/<int:package_id>/', views.bookings, name='users-bookings'),
    path('booking_success/<int:booking_id>/', views.booking_success, name='users-booking-success'),
    path('activate/<uid64>/<token>',views.ActivateAccountView.as_view(),name='activate'),
    path('docs/', views.documentation, name='documentation'),
    path('careers/', views.careers, name='careers'),
    path('careers/job/<slug:slug>/', views.job_detail, name='job_detail'),
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),

    # Quote Request URLs
    path('quote/', views.quote_request_view, name='quote_request'),
    path('quote/success/', views.quote_success, name='quote_success'),

    # User Profile URLs
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/bookings/', views.booking_history, name='booking_history'),
    path('profile/booking/<str:booking_reference>/', views.booking_detail, name='booking_detail'),
    path('profile/bucket-list/', views.bucket_list_view, name='bucket_list'),
    path('profile/bucket-list/add/', views.add_to_bucket_list, name='add_to_bucket_list'),
    path('profile/bucket-list/remove/<int:item_id>/', views.remove_from_bucket_list, name='remove_from_bucket_list'),

    # Modern Checkout URLs
    path('book/<int:package_id>/', checkout_views.add_to_cart, name='add_to_cart'),
    path('checkout/customize/<int:package_id>/', checkout_views.checkout_customize, name='checkout_customize'),
    path('checkout/details/', checkout_views.checkout_details, name='checkout_details'),
    path('checkout/summary/', checkout_views.checkout_summary, name='checkout_summary'),
    path('booking/confirmation/<str:booking_reference>/', checkout_views.booking_confirmation, name='booking_confirmation'),

    # Cart Management URLs
    path('cart/remove/<int:package_id>/', checkout_views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:package_id>/', checkout_views.update_cart_item, name='update_cart_item'),

    # Test Error Pages (for development/testing only)
    path('test-500-error/', views.test_500_error, name='test_500_error'),
]
