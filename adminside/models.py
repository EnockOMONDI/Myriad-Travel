from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.html import strip_tags
from django.utils import timezone
from pyuploadcare.dj.models import ImageField
from django_ckeditor_5.fields import CKEditor5Field


class TravelCollection(models.Model):
    SECTION_CHOICES = [
        ('kenya', 'Explore Kenya'), ('world', 'Explore The World'),
        ('safaris', 'Tours & Safaris'), ('themes', 'Themed Packages'),
    ]
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    section = models.CharField(max_length=12, choices=SECTION_CHOICES)
    description = models.TextField(blank=True)
    packages = models.ManyToManyField('Package', blank=True, related_name='collections')
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    show_in_navigation = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('users:travel_collection', args=[self.slug])


class Campaign(models.Model):
    MAX_ACTIVE_CAMPAIGNS = 12
    title = models.CharField(max_length=160)
    package = models.ForeignKey('Package', on_delete=models.PROTECT, related_name='campaigns')
    starts_on = models.DateField(help_text='First day to display this campaign.')
    ends_on = models.DateField(help_text='Last day to display this campaign.')
    travel_dates = models.CharField(max_length=120, blank=True)
    display_order = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['display_order', 'pk']
        constraints = [models.CheckConstraint(
            check=models.Q(ends_on__gte=models.F('starts_on')),
            name='campaign_dates_in_order',
        )]

    def clean(self):
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValidationError({'ends_on': 'End date must be on or after start date.'})
        if self.is_active and self.package_id and self.package.status != 'published':
            raise ValidationError({'package': 'Choose a published package for an active campaign.'})
        if self.is_active:
            active_count = type(self).objects.filter(is_active=True).exclude(pk=self.pk).count()
            if active_count >= self.MAX_ACTIVE_CAMPAIGNS:
                raise ValidationError({
                    'is_active': f'Only {self.MAX_ACTIVE_CAMPAIGNS} active campaigns are allowed. Deactivate another campaign first.',
                })

    def __str__(self):
        return self.title

    @property
    def public_status(self):
        """Human-readable deal state used by admin and the public deals page."""
        today = timezone.localdate()
        if self.ends_on < today:
            return 'Expired'
        if self.starts_on > today:
            return 'Scheduled'
        if (self.ends_on - today).days <= 7:
            return 'Closing soon'
        if (today - self.starts_on).days <= 7:
            return 'New'
        return 'Active'


class PackageCategory(models.Model):
    """
    Category model for organizing packages (e.g., Nairobi Excursions, Kenya Safaris, Outbound)
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True, help_text="Category description")
    is_active = models.BooleanField(default=True)
    show_in_navigation = models.BooleanField(
        default=True,
        help_text='Show this category in relevant public navigation menus.',
    )
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


class PackingListItem(models.Model):
    """Reusable packing guidance that admins can attach to many packages."""
    name = models.CharField(max_length=160, unique=True)
    display_order = models.PositiveIntegerField(default=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name



class Destination(models.Model):
    """
    Hierarchical destination model: Country -> City -> Place, with optional
    multi-country travel areas that can link to several country records.
    """
    COUNTRY = 'country'
    CITY = 'city'
    PLACE = 'place'
    
    DESTINATION_TYPES = [
        (COUNTRY, 'Country'),
        (CITY, 'City'),
        (PLACE, 'Place'),
    ]

    REGION_CHOICES = [
        ('kenya', 'Kenya'),
        ('africa', 'Africa'),
        ('americas', 'Americas'),
        ('asia', 'Asia'),
        ('australasia', 'Australasia'),
        ('europe', 'Europe'),
        ('indian-ocean-islands', 'Indian Ocean Islands'),
        ('middle-east', 'Middle East'),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    destination_type = models.CharField(max_length=10, choices=DESTINATION_TYPES)
    region = models.CharField(max_length=32, choices=REGION_CHOICES, blank=True,
                              help_text='Used to place this destination in public navigation.')
    description = CKEditor5Field(config_name='default', help_text="Detailed destination description with rich text formatting")
    things_to_do = models.JSONField(
        default=list,
        blank=True,
        help_text='Enter a JSON list of practical activities, for example ["Beach time", "Boat trip"].',
    )
    image = ImageField(blank=True, null=True, manual_crop="4:4")
    
    # Hierarchical relationship
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    is_multi_country = models.BooleanField(
        default=False,
        help_text='Use this for a travel area that covers more than one country, such as the Caribbean or Arabian Gulf.',
    )
    member_countries = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='multi_country_groups',
        limit_choices_to={'destination_type': COUNTRY},
        help_text='Choose the existing country records covered by this travel area. Leave empty when the area still needs review.',
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
    show_in_navigation = models.BooleanField(
        default=True,
        help_text='Allow this destination to appear in public navigation after it has a published package.',
    )
    
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
        if self.is_multi_country and self.destination_type != self.COUNTRY:
            raise ValidationError("Multi-country groups must use Country as their destination type")
        if self.destination_type == self.COUNTRY and self.parent:
            raise ValidationError("Countries cannot have parent destinations")
        if self.destination_type == self.CITY and (not self.parent or self.parent.destination_type != self.COUNTRY):
            raise ValidationError("Cities must have a country as parent")
        if self.destination_type == self.PLACE and (
            not self.parent or self.parent.destination_type not in {self.CITY, self.COUNTRY}
        ):
            raise ValidationError("Places must have a country or city as parent")
        if self.is_featured and self.is_active:
            featured_count = type(self).objects.filter(
                is_featured=True,
                is_active=True,
            ).exclude(pk=self.pk).count()
            if featured_count >= 6:
                raise ValidationError('You can highlight a maximum of six active destinations on the public site.')

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
        return reverse('users:destination_detail', kwargs={'slug': self.slug})

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
        if self.is_multi_country:
            return None
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
        return '/static/images/hero/discover-kenya.jpeg'


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
        return '/static/images/placeholders/myriad-package-placeholder.png'

    def get_absolute_url(self):
        return reverse('accommodation_detail', kwargs={'slug': self.slug})


class TravelMode(models.Model):
    """
    Renamed from Travel - represents transportation options
    """
    FLIGHT = 'flight'
    CHARTER_FLIGHT = 'charter-flight'
    TRAIN = 'train'
    BUS = 'bus'
    CAR = 'car'
    BOAT = 'boat'
    TOUR_VAN = 'tour-van'
    CRUISE_SHIP = 'cruise-ship'
    CRUISER = 'cruiser'

    TRANSPORT_TYPES = [
        (FLIGHT, 'Flight'),
        (CHARTER_FLIGHT, 'Charter Flight'),
        (TRAIN, 'Train'),
        (BUS, 'Bus'),
        (CAR, 'Vehicle / Car'),
        (BOAT, 'Boat / Ferry'),
        (TOUR_VAN, 'Tour Van'),
        (CRUISE_SHIP, 'Cruise Ship'),
        (CRUISER, '4x4 Cruiser'),
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
    subtitle = models.CharField(max_length=280, blank=True, help_text="Short package card subtitle for the public website")
    description = CKEditor5Field(config_name='default', help_text="Detailed package description with rich text formatting")

    REGION_CHOICES = [
        ('kenya-safari', 'Kenya Safaris & Bush'),
        ('kenya-coast', 'Kenya Coast & Beach'),
        ('international', 'International Escapes'),
        ('day-trips', 'Weekend Hikes & Day Trips'),
    ]
    region = models.CharField(
        max_length=40,
        choices=REGION_CHOICES,
        default='kenya-safari',
        help_text="Frontend collection used by the Myriad package filters"
    )

    # Category
    category = models.ForeignKey(
        PackageCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='packages',
        help_text="Package category (e.g., Nairobi Excursions, Kenya Safaris, Outbound)"
    )
    categories = models.ManyToManyField(
        PackageCategory,
        blank=True,
        related_name='tagged_packages',
        help_text='Additional public categories. The primary category remains the main card label.',
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
    PRICE_CURRENCY_CHOICES = [
        ('KES', 'Kenyan Shillings (KES)'),
        ('USD', 'US Dollars (USD)'),
    ]
    price_currency = models.CharField(
        max_length=3,
        choices=PRICE_CURRENCY_CHOICES,
        default='KES',
        help_text='Currency for the stored adult sharing rate. Use the currency shown on the approved offer.',
    )
    adult_price = models.PositiveIntegerField()
    child_price = models.PositiveIntegerField()
    single_occupancy_supplement = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Optional supplement added to the adult sharing rate for a private room. Leave blank when unavailable.',
    )
    lipa_pole_pole = models.BooleanField(default=False, help_text="Show this package as eligible for Myriad's Lipa Pole Pole plan")
    lipa_pole_pole_months = models.PositiveIntegerField(default=4, help_text="Suggested number of monthly installments")

    # Package content
    highlights = models.TextField(blank=True, help_text="One public-facing highlight per line for package cards and detail pages")
    inclusions = CKEditor5Field(config_name='default', help_text="What's included in the package")
    exclusions = CKEditor5Field(config_name='default', help_text="What's NOT included in the package")
    travel_notes = models.TextField(
        blank=True,
        help_text='One traveller note per line. Example: Road conditions, limited network, weather or timing guidance.',
    )
    packing_items = models.ManyToManyField(
        PackingListItem,
        blank=True,
        related_name='packages',
        help_text='Select reusable items for this package. Add package-specific items in the field below.',
    )
    packing_list_custom = models.TextField(
        blank=True,
        help_text='Optional extra packing items, separated by commas or line breaks.',
    )
    
    # Media
    featured_image = ImageField(
        blank=True,
        null=True,
        manual_crop="4:4,16:10,16:9,4:3,3:2,1:1,9:16,4:5",
        help_text="Package image. Uploadcare crop options include square, card, hero and poster ratios.",
    )
    
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
    home_rank = models.PositiveIntegerField(
        default=100,
        help_text="Homepage selling order. Lower numbers appear first in the homepage package showcase."
    )
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    meta_keywords = models.TextField(
        blank=True,
        help_text='Optional comma-separated search phrases. Example: Chalbi Desert, Northern Kenya safari, Lake Turkana.',
    )
    aeo_summary = models.TextField(
        blank=True,
        help_text='A concise answer for search assistants. Example: A 5-day northern Kenya adventure from Nairobi to Chalbi, Lake Turkana and Marsabit.',
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['home_rank', '-is_featured', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['category', 'status']),
            models.Index(fields=['main_destination', 'status']),
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['status', 'home_rank']),
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
        return reverse('users:package_detail', kwargs={'slug': self.slug})

    @property
    def is_published(self):
        return self.status == self.PUBLISHED

    @property
    def has_single_occupancy(self):
        return self.single_occupancy_supplement is not None

    @property
    def single_occupancy_price(self):
        if not self.has_single_occupancy:
            return None
        return self.adult_price + self.single_occupancy_supplement

    def packing_list(self):
        selected = list(self.packing_items.filter(is_active=True).values_list('name', flat=True))
        custom = [item.strip() for item in self.packing_list_custom.replace('\n', ',').split(',') if item.strip()]
        return selected + [item for item in custom if item not in selected]


class PackageGalleryImage(models.Model):
    """
    Additional package photos used for past-trip galleries.
    """
    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        related_name='gallery_images'
    )
    image = ImageField(
        manual_crop="16:9,4:3,3:2,1:1,4:5,9:16",
        help_text="Gallery image. Use landscape for wide trip scenes or portrait for poster-style moments."
    )
    title = models.CharField(max_length=160, blank=True)
    caption = models.TextField(blank=True)
    location = models.CharField(max_length=160, blank=True)
    captured_at = models.DateField(null=True, blank=True)
    display_order = models.PositiveIntegerField(default=100)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', '-captured_at', '-created_at']
        indexes = [
            models.Index(fields=['package', 'is_visible', 'display_order']),
            models.Index(fields=['package', 'captured_at']),
        ]

    def clean(self):
        """Keep published packages complete enough for public discovery."""
        if self.status != self.PUBLISHED:
            return

        errors = {}
        if not self.main_destination_id:
            errors['main_destination'] = 'A published package needs a destination.'
        elif not self.main_destination.is_active:
            errors['main_destination'] = 'Choose an active destination before publishing.'

        if not self.category_id:
            errors['category'] = 'A published package needs a category for public filters.'
        elif not self.category.is_active:
            errors['category'] = 'Choose an active category before publishing.'

        for field in ('description', 'inclusions', 'exclusions'):
            value = str(getattr(self, field, '') or '')
            if not strip_tags(value).replace('\xa0', ' ').strip():
                errors[field] = 'This public package content is required before publishing.'

        if errors:
            raise ValidationError(errors)
        verbose_name = "Package Gallery Image"
        verbose_name_plural = "Package Gallery Images"

    def __str__(self):
        return self.title or f"{self.package.name} gallery image"

    def get_image_url(self):
        if self.image:
            return self.image.cdn_url
        return '/static/images/placeholders/myriad-package-placeholder.png'


class PackageDeparture(models.Model):
    """A dated or scheduled departure attached to a package."""
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='departures')
    label = models.CharField(max_length=160, blank=True)
    starts_on = models.DateField()
    ends_on = models.DateField()
    departure_location = models.CharField(max_length=160, blank=True)
    departure_time = models.TimeField(null=True, blank=True)
    return_location = models.CharField(max_length=160, blank=True)
    return_time_note = models.CharField(max_length=160, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ['display_order', 'starts_on']
        constraints = [models.CheckConstraint(
            check=models.Q(ends_on__gte=models.F('starts_on')),
            name='package_departure_dates_in_order',
        )]

    def __str__(self):
        return self.label or f'{self.package.name} ({self.starts_on} - {self.ends_on})'

    @property
    def date_label(self):
        return f'{self.starts_on:%-d}–{self.ends_on:%-d %B %Y}'


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
    date = models.DateField(null=True, blank=True)
    theme = models.CharField(max_length=160, blank=True)
    route = models.CharField(max_length=240, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    summary = models.TextField(blank=True)
    main_activities = models.TextField(blank=True, help_text='One confirmed activity per line.')
    optional_activities = models.TextField(blank=True, help_text='One optional activity per line.')
    overnight_location = models.CharField(max_length=200, blank=True)
    operational_notes = models.TextField(blank=True)
    estimated_departure_time = models.TimeField(null=True, blank=True)
    estimated_arrival_time = models.TimeField(null=True, blank=True)
    
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
        return '/static/images/placeholders/myriad-package-placeholder.png'
