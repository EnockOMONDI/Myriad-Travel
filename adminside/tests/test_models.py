"""
Unit tests for adminside app models
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from datetime import date

from adminside.models import (
    Destination, Package, Accommodation, TravelMode,
    ItineraryDay, PackageBooking, Itinerary
)


class DestinationModelTest(TestCase):
    """Test cases for Destination model"""
    
    def setUp(self):
        """Set up test data"""
        self.country = Destination.objects.create(
            name='Kenya',
            slug='kenya',
            destination_type=Destination.COUNTRY,
            description='Beautiful East African country',
            starting_price=Decimal('500.00')
        )
        
        self.city = Destination.objects.create(
            name='Nairobi',
            slug='nairobi',
            destination_type=Destination.CITY,
            description='Capital city of Kenya',
            parent=self.country,
            starting_price=Decimal('300.00')
        )
    
    def test_destination_creation(self):
        """Test basic destination creation"""
        self.assertEqual(self.country.name, 'Kenya')
        self.assertEqual(self.country.destination_type, Destination.COUNTRY)
        self.assertIsNone(self.country.parent)
        self.assertEqual(self.country.starting_price, Decimal('500.00'))
    
    def test_destination_hierarchy(self):
        """Test destination hierarchy validation"""
        self.assertEqual(self.city.parent, self.country)
        self.assertEqual(self.city.destination_type, Destination.CITY)
    
    def test_destination_str_method(self):
        """Test destination string representation"""
        self.assertEqual(str(self.country), 'Kenya')
        self.assertEqual(str(self.city), 'Kenya, Nairobi')
    
    def test_get_full_name(self):
        """Test get_full_name method"""
        self.assertEqual(self.country.get_full_name(), 'Kenya')
        self.assertEqual(self.city.get_full_name(), 'Kenya, Nairobi')
    
    def test_country_property(self):
        """Test country property"""
        self.assertEqual(self.country.country, self.country)
        self.assertEqual(self.city.country, self.country)
    
    def test_destination_validation(self):
        """Test destination hierarchy validation"""
        # Country cannot have parent
        with self.assertRaises(ValidationError):
            invalid_country = Destination(
                name='Invalid Country',
                slug='invalid-country',
                destination_type=Destination.COUNTRY,
                parent=self.country,
                description='Invalid country with parent'
            )
            invalid_country.full_clean()
        
        # City must have country as parent
        with self.assertRaises(ValidationError):
            invalid_city = Destination(
                name='Invalid City',
                slug='invalid-city',
                destination_type=Destination.CITY,
                description='Invalid city without parent'
            )
            invalid_city.full_clean()


class PackageModelTest(TestCase):
    """Test cases for Package model"""
    
    def setUp(self):
        """Set up test data"""
        self.destination = Destination.objects.create(
            name='Maasai Mara',
            slug='maasai-mara',
            destination_type=Destination.PLACE,
            description='Famous wildlife reserve'
        )
        
        self.package = Package.objects.create(
            name='Maasai Mara Safari',
            slug='maasai-mara-safari',
            description='3-day wildlife safari',
            main_destination=self.destination,
            duration_days=3,
            duration_nights=2,
            adult_price=1500,
            child_price=1050,
            status=Package.PUBLISHED
        )
    
    def test_package_creation(self):
        """Test basic package creation"""
        self.assertEqual(self.package.name, 'Maasai Mara Safari')
        self.assertEqual(self.package.main_destination, self.destination)
        self.assertEqual(self.package.duration_days, 3)
        self.assertEqual(self.package.duration_nights, 2)
        self.assertEqual(self.package.adult_price, 1500)
        self.assertEqual(self.package.child_price, 1050)
        self.assertEqual(self.package.status, Package.PUBLISHED)
    
    def test_package_str_method(self):
        """Test package string representation"""
        expected = 'Maasai Mara Safari'
        self.assertEqual(str(self.package), expected)
    
    def test_package_slug_generation(self):
        """Test manual slug assignment"""
        package = Package.objects.create(
            name='Test Package Name',
            slug='test-package-name',  # Manual slug assignment
            description='Test description',
            main_destination=self.destination,
            duration_days=2,
            duration_nights=1,
            adult_price=1000,
            child_price=700,
            status=Package.DRAFT
        )
        self.assertEqual(package.slug, 'test-package-name')
    
    def test_package_status_choices(self):
        """Test package status field choices"""
        # Test draft status
        draft_package = Package.objects.create(
            name='Draft Package',
            description='Draft package description',
            main_destination=self.destination,
            duration_days=1,
            duration_nights=0,
            adult_price=500,
            child_price=350,
            status=Package.DRAFT
        )
        self.assertEqual(draft_package.status, Package.DRAFT)
        
        # Test published status
        self.assertEqual(self.package.status, Package.PUBLISHED)


class AccommodationModelTest(TestCase):
    """Test cases for Accommodation model"""
    
    def setUp(self):
        """Set up test data"""
        self.destination = Destination.objects.create(
            name='Nairobi',
            slug='nairobi',
            destination_type=Destination.CITY,
            description='Capital city of Kenya'
        )
        
        self.accommodation = Accommodation.objects.create(
            name='Safari Lodge',
            slug='safari-lodge',
            accommodation_type=Accommodation.LODGE,
            description='Luxury safari lodge',
            destination=self.destination,
            price_per_room_per_night=200,
            rating=4.5,
            is_featured=True
        )
    
    def test_accommodation_creation(self):
        """Test basic accommodation creation"""
        self.assertEqual(self.accommodation.name, 'Safari Lodge')
        self.assertEqual(self.accommodation.accommodation_type, Accommodation.LODGE)
        self.assertEqual(self.accommodation.destination, self.destination)
        self.assertEqual(self.accommodation.price_per_room_per_night, 200)
        self.assertEqual(self.accommodation.rating, 4.5)
        self.assertTrue(self.accommodation.is_featured)
    
    def test_accommodation_str_method(self):
        """Test accommodation string representation"""
        expected = f"Safari Lodge - {self.destination.name}"
        self.assertEqual(str(self.accommodation), expected)
    
    def test_accommodation_types(self):
        """Test accommodation type choices"""
        hotel = Accommodation.objects.create(
            name='City Hotel',
            accommodation_type=Accommodation.HOTEL,
            description='Modern city hotel',
            destination=self.destination,
            price_per_room_per_night=150
        )
        self.assertEqual(hotel.accommodation_type, Accommodation.HOTEL)


class TravelModeModelTest(TestCase):
    """Test cases for TravelMode model"""
    
    def setUp(self):
        """Set up test data"""
        self.travel_mode = TravelMode.objects.create(
            name='4WD Safari Vehicle',
            transport_type=TravelMode.CAR,
            departure_location='Nairobi',
            arrival_location='Maasai Mara',
            departure_time='08:00:00',
            arrival_time='12:00:00',
            duration_minutes=240,
            price_per_person=100,
            description='Comfortable safari vehicle',
            is_active=True
        )
    
    def test_travel_mode_creation(self):
        """Test basic travel mode creation"""
        self.assertEqual(self.travel_mode.name, '4WD Safari Vehicle')
        self.assertEqual(self.travel_mode.transport_type, TravelMode.CAR)
        self.assertEqual(self.travel_mode.departure_location, 'Nairobi')
        self.assertEqual(self.travel_mode.arrival_location, 'Maasai Mara')
        self.assertEqual(self.travel_mode.price_per_person, 100)
        self.assertTrue(self.travel_mode.is_active)
    
    def test_travel_mode_str_method(self):
        """Test travel mode string representation"""
        expected = '4WD Safari Vehicle - Nairobi to Maasai Mara'
        self.assertEqual(str(self.travel_mode), expected)


class ItineraryDayModelTest(TestCase):
    """Test cases for ItineraryDay model"""
    
    def setUp(self):
        """Set up test data"""
        self.destination = Destination.objects.create(
            name='Maasai Mara',
            slug='maasai-mara',
            destination_type=Destination.PLACE,
            description='Famous wildlife reserve'
        )
        
        self.package = Package.objects.create(
            name='Safari Package',
            slug='safari-package',
            description='Safari package description',
            main_destination=self.destination,
            duration_days=3,
            duration_nights=2,
            adult_price=1500,
            child_price=1050,
            status=Package.PUBLISHED
        )

        # Create itinerary first
        self.itinerary = Itinerary.objects.create(
            package=self.package
        )

        self.itinerary_day = ItineraryDay.objects.create(
            itinerary=self.itinerary,
            day_number=1,
            title='Arrival Day',
            description='Arrive at Maasai Mara and check in',
            destination=self.destination
        )
    
    def test_itinerary_day_creation(self):
        """Test basic itinerary day creation"""
        self.assertEqual(self.itinerary_day.itinerary, self.itinerary)
        self.assertEqual(self.itinerary_day.day_number, 1)
        self.assertEqual(self.itinerary_day.title, 'Arrival Day')
        self.assertEqual(self.itinerary_day.description, 'Arrive at Maasai Mara and check in')
        self.assertEqual(self.itinerary_day.destination, self.destination)
    
    def test_itinerary_day_str_method(self):
        """Test itinerary day string representation"""
        expected = 'Day 1: Arrival Day'
        self.assertEqual(str(self.itinerary_day), expected)
    
    def test_itinerary_day_ordering(self):
        """Test itinerary day ordering by day number"""
        day2 = ItineraryDay.objects.create(
            itinerary=self.itinerary,
            day_number=2,
            title='Safari Day',
            description='Full day safari'
        )

        day3 = ItineraryDay.objects.create(
            itinerary=self.itinerary,
            day_number=3,
            title='Departure Day',
            description='Check out and departure'
        )

        itinerary_days = list(ItineraryDay.objects.filter(itinerary=self.itinerary))
        self.assertEqual(itinerary_days[0].day_number, 1)
        self.assertEqual(itinerary_days[1].day_number, 2)
        self.assertEqual(itinerary_days[2].day_number, 3)


class PackageBookingModelTest(TestCase):
    """Test cases for PackageBooking model"""
    
    def setUp(self):
        """Set up test data"""
        self.destination = Destination.objects.create(
            name='Test Destination',
            slug='test-destination',
            destination_type=Destination.PLACE,
            description='Test destination'
        )
        
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
        
        self.accommodation = Accommodation.objects.create(
            name='Test Hotel',
            slug='test-hotel',
            description='Test hotel description',
            destination=self.destination,
            price_per_room_per_night=100
        )

        self.travel_mode = TravelMode.objects.create(
            name='Test Vehicle',
            transport_type=TravelMode.CAR,
            departure_location='Nairobi',
            arrival_location='Test Destination',
            departure_time='08:00:00',
            arrival_time='10:00:00',
            duration_minutes=120,
            price_per_person=50,
            description='Test vehicle description'
        )

        # Create a test user for PackageBooking
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_package_booking_creation(self):
        """Test basic package booking creation"""
        booking = PackageBooking.objects.create(
            package=self.package,
            user=self.user,
            adults_count=2,
            children_count=1,
            travel_date=date.today(),
            total_amount=2500,  # PositiveIntegerField expects integer
            status=PackageBooking.PENDING
        )

        self.assertEqual(booking.package, self.package)
        self.assertEqual(booking.user, self.user)
        self.assertEqual(booking.adults_count, 2)
        self.assertEqual(booking.children_count, 1)
        self.assertEqual(booking.total_amount, 2500)
        self.assertEqual(booking.status, PackageBooking.PENDING)
    
    def test_package_booking_str_method(self):
        """Test package booking string representation"""
        booking = PackageBooking.objects.create(
            package=self.package,
            user=self.user,
            adults_count=1,
            children_count=0,
            travel_date=date.today(),
            total_amount=1000
        )

        expected = f"Booking {booking.id} - {self.package.name} by {self.user.username}"
        self.assertEqual(str(booking), expected)
    
    def test_package_booking_with_accommodation(self):
        """Test package booking with selected accommodation"""
        booking = PackageBooking.objects.create(
            package=self.package,
            user=self.user,
            selected_accommodation=self.accommodation,
            adults_count=2,
            children_count=0,
            travel_date=date.today(),
            total_amount=2200
        )

        self.assertEqual(booking.selected_accommodation, self.accommodation)

    def test_package_booking_with_travel_mode(self):
        """Test package booking with selected travel mode"""
        booking = PackageBooking.objects.create(
            package=self.package,
            user=self.user,
            selected_travel_mode=self.travel_mode,
            adults_count=2,
            children_count=0,
            travel_date=date.today(),
            total_amount=2100
        )

        self.assertEqual(booking.selected_travel_mode, self.travel_mode)
