from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from pyuploadcare.dj.models import ImageField
from django_ckeditor_5.fields import CKEditor5Field


class PackageCategory(models.Model):
    """
    Category model for organizing packages (e.g., Nairobi Excursions, Kenya Safaris, Outbound)
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, help_text="Category description")
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0, help_text="Order of appearance (lower numbers appear first)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = "Package Category"
        verbose_name_plural = "Package Categories"
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Clean slug before saving"""
        if self.slug:
            self.slug = self.slug.replace('&', 'and').replace(' ', '-')
            self.slug = slugify(self.slug, allow_unicode=False)
        super().save(*args, **kwargs)

    def get_package_count(self):
        """Get count of published packages in this category"""
        return self.packages.filter(status='published').count()



class Destination(models.Model):
    """
    Hierarchical destination model: Country -> City -> Place
    """
    COUNTRY = 'country'
    CITY = 'city'
    PLACE = 'place'
    
    DESTINATION_TYPES = [
        (COUNTRY, 'Country'),
        (CITY, 'City'),
        (PLACE, 'Place'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    destination_type = models.CharField(max_length=10, choices=DESTINATION_TYPES)
    description = CKEditor5Field(config_name='default', help_text="Detailed destination description with rich text formatting")
    image = ImageField(blank=True, null=True, manual_crop="4:4")
    
    # Hierarchical relationship
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    
    # SEO and metadata
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    
    # Pricing information
    starting_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Starting price for packages to this destination (in USD)"
    )

    # Display order and featured status
    display_order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        indexes = [
            models.Index(fields=['destination_type', 'is_active']),
            models.Index(fields=['parent', 'is_active']),
        ]

    def clean(self):
        """Validate destination hierarchy"""
        if self.destination_type == self.COUNTRY and self.parent:
            raise ValidationError("Countries cannot have parent destinations")
        if self.destination_type == self.CITY and (not self.parent or self.parent.destination_type != self.COUNTRY):
            raise ValidationError("Cities must have a country as parent")
        if self.destination_type == self.PLACE and (not self.parent or self.parent.destination_type != self.CITY):
            raise ValidationError("Places must have a city as parent")

    def save(self, *args, **kwargs):
        """Clean slug before saving"""
        if self.slug:
            # Replace special characters that aren't allowed in Django slugs
            self.slug = self.slug.replace('&', 'and').replace(' ', '-')
            # Ensure slug only contains valid characters
            self.slug = slugify(self.slug, allow_unicode=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """Return full hierarchical name"""
        if self.parent:
            return f"{self.parent.get_full_name()}, {self.name}"
        return self.name

    def get_absolute_url(self):
        return reverse('destination_detail', kwargs={'slug': self.slug})

    def get_all_children(self):
        """Get all descendant destinations recursively"""
        children = []
        for child in self.children.filter(is_active=True):
            children.append(child)
            children.extend(child.get_all_children())
        return children

    @property
    def country(self):
        """Get the country for this destination"""
        if self.destination_type == self.COUNTRY:
            return self
        elif self.parent:
            return self.parent.country
        return None

    def get_all_children(self):
        """Get all descendant destinations"""
        children = list(self.children.filter(is_active=True))
        for child in list(children):
            children.extend(child.get_all_children())
        return children

    def get_image_url(self):
        """Get the image URL with fallback to default destination image"""
        if self.image:
            return self.image.cdn_url
        return '/static/assets/images/about/about-1.png'


class Accommodation(models.Model):
    """
    Hotel/Lodge accommodation model
    """
    HOTEL = 'hotel'
    LODGE = 'lodge'
    RESORT = 'resort'
    GUESTHOUSE = 'guesthouse'
    AIRBNB = 'airbnb'

    ACCOMMODATION_TYPES = [
        (HOTEL, 'Hotel'),
        (LODGE, 'Lodge'),
        (RESORT, 'Resort'),
        (GUESTHOUSE, 'Guest House'),
        (AIRBNB, 'Airbnb'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    accommodation_type = models.CharField(max_length=20, choices=ACCOMMODATION_TYPES, default=HOTEL)
    description = CKEditor5Field(config_name='default', help_text="Detailed accommodation description with rich text formatting")
    
    # Location
    destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name='accommodations'
    )
    address = models.TextField(blank=True)
    
    # Pricing and capacity
    price_per_room_per_night = models.PositiveIntegerField()
    max_occupancy_per_room = models.PositiveIntegerField(default=2)
    total_rooms = models.PositiveIntegerField(default=1)
    
    # Media
    image = ImageField(blank=False, null=False, manual_crop="4:4")
    
    # Features and amenities
    amenities = models.TextField(help_text="Comma-separated list of amenities")
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Ratings
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-rating', 'name']
        indexes = [
            models.Index(fields=['destination', 'is_active']),
            models.Index(fields=['accommodation_type', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
            models.Index(fields=['rating', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        """Clean slug before saving"""
        if self.slug:
            # Replace special characters that aren't allowed in Django slugs
            self.slug = self.slug.replace('&', 'and').replace(' ', '-')
            # Ensure slug only contains valid characters
            self.slug = slugify(self.slug, allow_unicode=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.destination.name}"

    def get_image_url(self):
        """Get the image URL with fallback to default accommodation image"""
        if self.image:
            return self.image.cdn_url
        return '/static/assets/images/about/accomodationdefault.png'

    def get_absolute_url(self):
        return reverse('accommodation_detail', kwargs={'slug': self.slug})


class TravelMode(models.Model):
    """
    Renamed from Travel - represents transportation options
    """
    FLIGHT = 'flight'
    TRAIN = 'train'
    BUS = 'bus'
    CAR = 'car'
    BOAT = 'boat'
    CRUISER = 'cruiser'

    TRANSPORT_TYPES = [
        (FLIGHT, 'Flight'),
        (TRAIN, 'Train'),
        (BUS, 'Bus'),
        (CAR, 'Car/Private Vehicle'),
        (BOAT, 'Boat/Ferry'),
        (CRUISER, 'Cruiser'),
    ]
    
    name = models.CharField(max_length=200)  # e.g., "Kenya Airways Morning Flight"
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_TYPES)
    
    # Route information
    departure_location = models.CharField(max_length=200)
    arrival_location = models.CharField(max_length=200)
    
    # Timing
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField()
    
    # Pricing
    price_per_person = models.PositiveIntegerField()
    child_discount_percentage = models.PositiveIntegerField(default=0)
    
    # Additional info
    description = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    
    # Capacity and availability
    total_capacity = models.PositiveIntegerField(default=50)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['transport_type', 'departure_time']
        indexes = [
            models.Index(fields=['transport_type', 'is_active']),
            models.Index(fields=['departure_location', 'arrival_location']),
        ]

    def __str__(self):
        return f"{self.name} - {self.departure_location} to {self.arrival_location}"

    @property
    def child_price(self):
        """Calculate child price based on discount"""
        return self.price_per_person * (100 - self.child_discount_percentage) // 100


class Package(models.Model):
    """
    Main travel package model with improved structure
    """
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PUBLISHED, 'Published'),
        (ARCHIVED, 'Archived'),
    ]
    
    # Basic information
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = CKEditor5Field(config_name='default', help_text="Detailed package description with rich text formatting")

    # Category
    category = models.ForeignKey(
        PackageCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='packages',
        help_text="Package category (e.g., Nairobi Excursions, Kenya Safaris, Outbound)"
    )

    # Destinations - simplified to main destination only
    # Sub-destinations will be handled through itinerary
    main_destination = models.ForeignKey(
        Destination,
        on_delete=models.CASCADE,
        related_name='packages',
        help_text="Primary destination for this package"
    )

    # Package details
    duration_days = models.PositiveIntegerField()
    duration_nights = models.PositiveIntegerField()

    # Pricing
    adult_price = models.PositiveIntegerField()
    child_price = models.PositiveIntegerField()

    # Package content
    inclusions = CKEditor5Field(config_name='default', help_text="What's included in the package")
    exclusions = CKEditor5Field(config_name='default', help_text="What's NOT included in the package")
    
    # Media
    featured_image = ImageField(blank=False, null=False, manual_crop="4:4")
    
    # Accommodation and travel options
    available_accommodations = models.ManyToManyField(
        Accommodation,
        related_name='packages',
        blank=True
    )
    available_travel_modes = models.ManyToManyField(
        TravelMode,
        related_name='packages',
        blank=True
    )
    
    # Bookings - handled through PackageBooking model
    
    # Statistics
    total_bookings = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=DRAFT)
    is_featured = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-is_featured', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['main_destination', 'status']),
            models.Index(fields=['status', 'is_featured']),
        ]

    def save(self, *args, **kwargs):
        """Clean slug before saving"""
        if self.slug:
            # Replace special characters that aren't allowed in Django slugs
            self.slug = self.slug.replace('&', 'and').replace(' ', '-')
            # Ensure slug only contains valid characters
            self.slug = slugify(self.slug, allow_unicode=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('package_detail', kwargs={'slug': self.slug})

    @property
    def is_published(self):
        return self.status == self.PUBLISHED


class Itinerary(models.Model):
    """
    One-to-one relationship with Package for detailed day-by-day planning
    """
    package = models.OneToOneField(
        Package,
        on_delete=models.CASCADE,
        related_name='itinerary'
    )
    title = models.CharField(max_length=200)
    overview = models.TextField(blank=True, help_text="Brief overview of the itinerary")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Itineraries"

    def __str__(self):
        return f"Itinerary for {self.package.name}"


class ItineraryDay(models.Model):
    """
    Renamed from ItineraryDescription for clarity
    """
    itinerary = models.ForeignKey(
        Itinerary,
        on_delete=models.CASCADE,
        related_name='days'
    )
    day_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Optional destination for this day
    destination = models.ForeignKey(
        Destination,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itinerary_days'
    )
    
    # Accommodation for this day (if different from package default)
    accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itinerary_days'
    )
    
    # Meals included
    breakfast = models.BooleanField(default=False)
    lunch = models.BooleanField(default=False)
    dinner = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_number']
        unique_together = ['itinerary', 'day_number']
        indexes = [
            models.Index(fields=['itinerary', 'day_number']),
        ]

    def __str__(self):
        return f"Day {self.day_number}: {self.title}"


class PackageBooking(models.Model):
    """
    Enhanced booking model to track selected options
    """
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
        (COMPLETED, 'Completed'),
    ]
    
    # Basic booking info
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='package_bookings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='package_bookings')
    
    # Selected options
    selected_accommodation = models.ForeignKey(
        Accommodation,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bookings'
    )
    selected_travel_mode = models.ForeignKey(
        TravelMode,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bookings'
    )
    
    # Guest details
    adults_count = models.PositiveIntegerField(default=1)
    children_count = models.PositiveIntegerField(default=0)
    
    # Dates
    travel_date = models.DateField()
    
    # Pricing
    total_amount = models.PositiveIntegerField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    
    # Additional info
    special_requests = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.id} - {self.package.name} by {self.user.username}"


class HeroSlider(models.Model):
    """
    Dynamic hero slider model for homepage management
    """
    title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Optional caption/title for the hero slide"
    )
    subtitle = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        help_text="Optional subtitle for the hero slide"
    )
    image = ImageField(
        manual_crop="2048x1080",
        help_text="Hero slider image (recommended size: 2048x1080px for optimal quality)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable this slide"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Order of appearance (lower numbers appear first)"
    )

    # Optional call-to-action
    cta_text = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Call-to-action button text (e.g., 'Book Now', 'Explore')"
    )
    cta_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL for the call-to-action button"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Hero Slider"
        verbose_name_plural = "Hero Sliders"

    def __str__(self):
        if self.title:
            return f"Hero Slide: {self.title}"
        return f"Hero Slide {self.id}"

    @classmethod
    def get_active_slides(cls):
        """Get all active slides ordered by their order field"""
        return cls.objects.filter(is_active=True).order_by('order')

    def get_image_url(self):
        """Get the image URL with fallback to default"""
        if self.image:
            return self.image.cdn_url
        return '/static/assets/images/hero/2.png'