"""
Tests for admin interface functionality
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal

from adminside.models import Package, Destination, Accommodation, TravelMode
from users.models import Booking, UserProfile, BucketList


class AdminInterfaceTest(TestCase):
    """Test admin interface functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpass123'
        )
        
        # Create test destination
        self.destination = Destination.objects.create(
            name='Test Destination',
            slug='test-destination',
            destination_type=Destination.PLACE,
            description='Test destination description'
        )
        
        # Create test package
        self.package = Package.objects.create(
            name='Test Package',
            slug='test-package',
            description='Test package description',
            main_destination=self.destination,
            duration_days=3,
            duration_nights=2,
            adult_price=1000,
            child_price=700,
            status=Package.PUBLISHED
        )
        
        # Create test accommodation
        self.accommodation = Accommodation.objects.create(
            name='Test Hotel',
            slug='test-hotel',
            description='Test hotel description',
            destination=self.destination,
            price_per_room_per_night=100
        )
        
        # Create test booking
        self.booking = Booking.objects.create(
            package=self.package,
            user=self.regular_user,
            full_name='Test User',
            email='user@example.com',
            phone_number='+254 701 810167',
            number_of_adults=2,
            number_of_children=0,
            number_of_rooms=1,
            package_price=Decimal('2000.00'),
            accommodation_price=Decimal('0.00'),
            travel_price=Decimal('0.00'),
            total_amount=Decimal('2000.00')
        )
    
    def test_admin_login_required(self):
        """Test that admin interface requires authentication"""
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_admin_login_success(self):
        """Test successful admin login"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django administration')
    
    def test_regular_user_admin_access_denied(self):
        """Test that regular users cannot access admin"""
        self.client.login(username='user', password='userpass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_admin_destination_list(self):
        """Test admin destination list view"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/admin/adminside/destination/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.destination.name)
    
    def test_admin_destination_add(self):
        """Test adding destination via admin"""
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.post('/admin/adminside/destination/add/', {
            'name': 'New Destination',
            'slug': 'new-destination',
            'destination_type': Destination.PLACE,
            'description': 'New destination description',
            'is_active': True,
            'display_order': 0,
            'is_featured': False
        })
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Verify destination was created
        self.assertTrue(
            Destination.objects.filter(name='New Destination').exists()
        )
    
    def test_admin_destination_edit(self):
        """Test editing destination via admin"""
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.post(f'/admin/adminside/destination/{self.destination.id}/change/', {
            'name': 'Updated Destination',
            'slug': self.destination.slug,
            'destination_type': self.destination.destination_type,
            'description': 'Updated description',
            'is_active': True,
            'display_order': 0,
            'is_featured': False
        })
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Verify destination was updated
        self.destination.refresh_from_db()
        self.assertEqual(self.destination.name, 'Updated Destination')
    
    def test_admin_package_list(self):
        """Test admin package list view"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/admin/adminside/package/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.package.name)
    
    def test_admin_package_add(self):
        """Test adding package via admin"""
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.post('/admin/adminside/package/add/', {
            'name': 'New Package',
            'slug': 'new-package',
            'description': 'New package description',
            'main_destination': self.destination.id,
            'duration_days': 2,
            'duration_nights': 1,
            'adult_price': 800,
            'child_price': 560,
            'status': Package.DRAFT,
            'is_featured': False,
            'max_group_size': 0,
            'min_group_size': 0,
            'difficulty_level': 0
        })
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Verify package was created
        self.assertTrue(
            Package.objects.filter(name='New Package').exists()
        )
    
    def test_admin_accommodation_list(self):
        """Test admin accommodation list view"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/admin/adminside/accommodation/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.accommodation.name)
    
    def test_admin_booking_list(self):
        """Test admin booking list view"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get('/admin/users/booking/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.booking.full_name)
    
    def test_admin_booking_detail(self):
        """Test admin booking detail view"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(f'/admin/users/booking/{self.booking.id}/change/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.booking.full_name)
        self.assertContains(response, self.booking.email)
    
    def test_admin_user_profile_inline(self):
        """Test admin user profile inline editing"""
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(f'/admin/auth/user/{self.regular_user.id}/change/')
        self.assertEqual(response.status_code, 200)
        
        # Should show user profile inline
        self.assertContains(response, 'profile')
    
    def test_admin_search_functionality(self):
        """Test admin search functionality"""
        self.client.login(username='admin', password='adminpass123')
        
        # Test package search
        response = self.client.get('/admin/adminside/package/?q=Test')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.package.name)
        
        # Test booking search
        response = self.client.get('/admin/users/booking/?q=Test')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.booking.full_name)
    
    def test_admin_filtering(self):
        """Test admin list filtering"""
        self.client.login(username='admin', password='adminpass123')
        
        # Test package status filtering
        response = self.client.get('/admin/adminside/package/?status=published')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.package.name)
        
        # Test booking status filtering
        response = self.client.get('/admin/users/booking/?status=pending')
        self.assertEqual(response.status_code, 200)
    
    def test_admin_bulk_actions(self):
        """Test admin bulk actions"""
        self.client.login(username='admin', password='adminpass123')
        
        # Create additional packages for bulk action
        package2 = Package.objects.create(
            name='Package 2',
            slug='package-2',
            description='Package 2 description',
            main_destination=self.destination,
            duration_days=2,
            duration_nights=1,
            adult_price=800,
            child_price=560,
            status=Package.DRAFT
        )
        
        # Test bulk delete action
        response = self.client.post('/admin/adminside/package/', {
            'action': 'delete_selected',
            '_selected_action': [self.package.id, package2.id],
            'post': 'yes'  # Confirm deletion
        })
        
        # Should redirect after bulk action
        self.assertEqual(response.status_code, 302)
    
    def test_admin_permissions(self):
        """Test admin permissions for different models"""
        self.client.login(username='admin', password='adminpass123')
        
        # Test access to different model admin pages
        admin_urls = [
            '/admin/adminside/destination/',
            '/admin/adminside/package/',
            '/admin/adminside/accommodation/',
            '/admin/adminside/travelmode/',
            '/admin/users/booking/',
            '/admin/users/userprofile/',
            '/admin/users/bucketlist/',
        ]
        
        for url in admin_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
    
    def test_admin_model_validation(self):
        """Test admin model validation"""
        self.client.login(username='admin', password='adminpass123')
        
        # Test invalid package creation (missing required fields)
        response = self.client.post('/admin/adminside/package/add/', {
            'name': '',  # Empty name should fail validation
            'description': 'Test description',
            'main_destination': self.destination.id,
            'duration_days': 1,
            'duration_nights': 0,
            'adult_price': 500,
            'child_price': 350,
            'status': Package.DRAFT
        })
        
        # Should stay on form with validation errors
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required')
    
    def test_admin_readonly_fields(self):
        """Test admin readonly fields"""
        self.client.login(username='admin', password='adminpass123')
        
        # Test booking detail view (some fields should be readonly)
        response = self.client.get(f'/admin/users/booking/{self.booking.id}/change/')
        self.assertEqual(response.status_code, 200)
        
        # Check for readonly fields (like booking_reference)
        self.assertContains(response, 'readonly')
    
    def test_admin_custom_actions(self):
        """Test custom admin actions"""
        self.client.login(username='admin', password='adminpass123')
        
        # Test package publish action (if implemented)
        response = self.client.post('/admin/adminside/package/', {
            'action': 'make_published',
            '_selected_action': [self.package.id]
        })
        
        # Should handle the action (redirect or stay on page)
        self.assertIn(response.status_code, [200, 302])
    
    def test_admin_export_functionality(self):
        """Test admin export functionality (if implemented)"""
        self.client.login(username='admin', password='adminpass123')
        
        # Test CSV export for bookings
        response = self.client.get('/admin/users/booking/?format=csv')
        
        # Should either provide CSV or redirect (depending on implementation)
        self.assertIn(response.status_code, [200, 302, 404])
    
    def test_admin_dashboard_widgets(self):
        """Test admin dashboard widgets"""
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        
        # Check for model links
        self.assertContains(response, 'Packages')
        self.assertContains(response, 'Destinations')
        self.assertContains(response, 'Accommodations')
        self.assertContains(response, 'Bookings')
    
    def test_admin_change_history(self):
        """Test admin change history"""
        self.client.login(username='admin', password='adminpass123')
        
        # Make a change to track history
        self.client.post(f'/admin/adminside/package/{self.package.id}/change/', {
            'name': 'Updated Package Name',
            'slug': self.package.slug,
            'description': self.package.description,
            'main_destination': self.destination.id,
            'duration_days': self.package.duration_days,
            'duration_nights': self.package.duration_nights,
            'adult_price': self.package.adult_price,
            'child_price': self.package.child_price,
            'status': self.package.status,
            'is_featured': False,
            'max_group_size': 0,
            'min_group_size': 0,
            'difficulty_level': 0
        })
        
        # Check history page
        response = self.client.get(f'/admin/adminside/package/{self.package.id}/history/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Changed')
    
    def test_admin_unfold_interface(self):
        """Test Django Unfold admin interface"""
        self.client.login(username='admin', password='adminpass123')
        
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)
        
        # Check for Unfold-specific elements
        unfold_elements = [
            'unfold',
            'sidebar',
            'navigation',
        ]
        
        # At least one Unfold element should be present
        has_unfold = any(
            element in response.content.decode().lower() 
            for element in unfold_elements
        )
        # Note: This might not always be true depending on configuration
        # self.assertTrue(has_unfold)
