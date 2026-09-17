from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import BigAutoField
from django_ckeditor_5.fields import CKEditor5Field
import uuid
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver



class UserBookings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey("adminside.Package", on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    number_of_adults = models.PositiveIntegerField()
    number_of_children = models.PositiveIntegerField(blank=True, null=True)
    number_of_rooms = models.PositiveIntegerField(default=1)
    booking_date = models.DateField(auto_now_add=True)
    include_travelling = models.BooleanField(default=False)
    special_requests = CKEditor5Field(config_name='default', blank=True, null=True, help_text="Any special requests or requirements")
    paid=models.BooleanField(default=False)
    total_amount = models.PositiveIntegerField(default=0, blank=True, null=True)


    class Meta:
        ordering = ('-booking_date', )

    def __str__(self):
        return f"Booking for {self.full_name}  {self.package.name} on {self.booking_date}"


class Booking(models.Model):
    """
    Modern booking model for guest and registered users
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

    # Booking identification
    booking_reference = models.CharField(max_length=20, unique=True, editable=False)

    # Package and user information
    package = models.ForeignKey("adminside.Package", on_delete=models.CASCADE, related_name='modern_bookings')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='modern_bookings')

    # Guest information (required for all bookings)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)

    # Traveler details
    number_of_adults = models.PositiveIntegerField(default=1)
    number_of_children = models.PositiveIntegerField(default=0)
    number_of_rooms = models.PositiveIntegerField(default=1)

    # Selected add-ons
    selected_accommodations = models.ManyToManyField(
        "adminside.Accommodation",
        blank=True,
        related_name='modern_bookings'
    )
    selected_travel_modes = models.ManyToManyField(
        "adminside.TravelMode",
        blank=True,
        related_name='modern_bookings'
    )

    # Pricing
    package_price = models.DecimalField(max_digits=10, decimal_places=2)
    accommodation_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    travel_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Additional information
    special_requests = CKEditor5Field(config_name='default', blank=True, null=True)
    travel_date = models.DateField(null=True, blank=True)

    # Status and timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Email tracking
    confirmation_email_sent = models.BooleanField(default=False)
    admin_notification_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        super().save(*args, **kwargs)

    def generate_booking_reference(self):
        """Generate unique booking reference"""
        import random
        import string
        while True:
            reference = 'NVT' + ''.join(random.choices(string.digits, k=7))
            if not Booking.objects.filter(booking_reference=reference).exists():
                return reference

    def calculate_total(self):
        """Calculate total booking amount"""
        total = self.package_price
        total += self.accommodation_price
        total += self.travel_price
        return total

    def __str__(self):
        return f"Booking {self.booking_reference} - {self.full_name}"


class GuestBooking(models.Model):
    """
    Temporary booking model for session-based cart system
    """
    session_key = models.CharField(max_length=40)
    package = models.ForeignKey("adminside.Package", on_delete=models.CASCADE)

    # Selected add-ons (stored as JSON or comma-separated IDs)
    selected_accommodation_ids = models.TextField(blank=True, default='')
    selected_travel_mode_ids = models.TextField(blank=True, default='')

    # Traveler details
    number_of_adults = models.PositiveIntegerField(default=1)
    number_of_children = models.PositiveIntegerField(default=0)
    number_of_rooms = models.PositiveIntegerField(default=1)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['session_key', 'package']

    def get_selected_accommodations(self):
        """Get selected accommodation objects"""
        if not self.selected_accommodation_ids:
            return []
        from adminside.models import Accommodation
        ids = [int(id.strip()) for id in self.selected_accommodation_ids.split(',') if id.strip()]
        return Accommodation.objects.filter(id__in=ids)

    def get_selected_travel_modes(self):
        """Get selected travel mode objects"""
        if not self.selected_travel_mode_ids:
            return []
        from adminside.models import TravelMode
        ids = [int(id.strip()) for id in self.selected_travel_mode_ids.split(',') if id.strip()]
        return TravelMode.objects.filter(id__in=ids)

    def calculate_total_price(self):
        """Calculate total price for this booking"""
        total = Decimal(str(self.package.adult_price)) * self.number_of_adults

        # Add children pricing (usually discounted)
        if self.number_of_children > 0:
            child_price = Decimal(str(self.package.child_price)) if hasattr(self.package, 'child_price') else Decimal(str(self.package.adult_price)) * Decimal('0.7')
            total += child_price * self.number_of_children

        # Add accommodation costs
        for accommodation in self.get_selected_accommodations():
            total += Decimal(str(accommodation.price_per_room_per_night)) * self.number_of_rooms * self.package.duration_days

        # Add travel costs
        for travel_mode in self.get_selected_travel_modes():
            total += Decimal(str(travel_mode.price_per_person)) * (self.number_of_adults + self.number_of_children)

        return total

    def __str__(self):
        return f"Guest Booking - {self.package.name} ({self.session_key[:8]}...)"


# users/models.py
class MICEInquiry(models.Model):
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    event_type = models.CharField(max_length=50, choices=[
        ('Meeting', 'Meeting'),
        ('Incentive', 'Incentive'),
        ('Conference', 'Conference'),
        ('Exhibition', 'Exhibition')
    ])
    attendees = models.PositiveIntegerField()
    event_details = CKEditor5Field(config_name='default', help_text="Detailed event information and requirements")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_name} - {self.event_type}"


class StudentTravelInquiry(models.Model):
    school_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    program_stage = models.CharField(max_length=50, choices=[
        ('Registration & Training', 'Registration & Training'),
        ('Regional Round', 'Regional Round'),
        ('Global Round', 'Global Round'),
        ('Tournament of Champions', 'Tournament of Champions')
    ])
    number_of_students = models.PositiveIntegerField()
    travel_details = CKEditor5Field(config_name='default', help_text="Detailed travel requirements and information")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.school_name} - {self.program_stage}"


class NGOTravelInquiry(models.Model):
    organization_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    organization_type = models.CharField(max_length=50, choices=[
        ('NGO', 'Non-Governmental Organization'),
        ('Humanitarian', 'Humanitarian Organization'),
        ('Charity', 'Charity Organization'),
        ('Development', 'Development Agency'),
        ('Relief', 'Relief Organization'),
        ('Other', 'Other')
    ])
    travel_purpose = models.CharField(max_length=100, choices=[
        ('Emergency Response', 'Emergency Response'),
        ('Field Operations', 'Field Operations'),
        ('Volunteer Coordination', 'Volunteer Coordination'),
        ('Project Implementation', 'Project Implementation'),
        ('Capacity Building', 'Capacity Building'),
        ('Monitoring & Evaluation', 'Monitoring & Evaluation'),
        ('Other', 'Other')
    ])
    number_of_travelers = models.PositiveIntegerField()
    travel_details = CKEditor5Field(config_name='default', help_text="Detailed travel requirements and information")
    sustainability_requirements = models.BooleanField(default=False, help_text="Do you require sustainable travel options?")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.organization_name} - {self.travel_purpose}"


class UserProfile(models.Model):
    """
    Extended user profile for additional information and preferences
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    passport_number = models.CharField(max_length=50, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)

    # Travel preferences
    preferred_travel_style = models.CharField(
        max_length=50,
        choices=[
            ('budget', 'Budget Travel'),
            ('mid_range', 'Mid-Range'),
            ('luxury', 'Luxury'),
            ('adventure', 'Adventure'),
            ('cultural', 'Cultural'),
            ('wildlife', 'Wildlife Safari'),
            ('beach', 'Beach & Relaxation'),
        ],
        blank=True,
        null=True
    )

    dietary_requirements = models.TextField(blank=True, null=True, help_text="Any dietary restrictions or preferences")
    special_needs = models.TextField(blank=True, null=True, help_text="Any special assistance requirements")

    # Account settings
    email_notifications = models.BooleanField(default=True, help_text="Receive email notifications about bookings and offers")
    marketing_emails = models.BooleanField(default=False, help_text="Receive marketing emails and travel deals")

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - Profile"

    @property
    def total_bookings(self):
        """Get total number of bookings for this user"""
        return Booking.objects.filter(user=self.user).count()

    @property
    def total_spent(self):
        """Get total amount spent by this user"""
        bookings = Booking.objects.filter(user=self.user)
        return sum(booking.total_amount for booking in bookings)


class BucketList(models.Model):
    """
    User's travel bucket list for packages and accommodations
    """
    ITEM_TYPES = [
        ('package', 'Travel Package'),
        ('accommodation', 'Accommodation'),
        ('destination', 'Destination'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bucket_list')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)

    # Foreign keys to different models (only one will be used per item)
    package = models.ForeignKey('adminside.Package', on_delete=models.CASCADE, blank=True, null=True)
    accommodation = models.ForeignKey('adminside.Accommodation', on_delete=models.CASCADE, blank=True, null=True)
    destination = models.ForeignKey('adminside.Destination', on_delete=models.CASCADE, blank=True, null=True)

    # Additional notes
    notes = models.TextField(blank=True, null=True, help_text="Personal notes about this bucket list item")
    priority = models.CharField(
        max_length=10,
        choices=[
            ('high', 'High Priority'),
            ('medium', 'Medium Priority'),
            ('low', 'Low Priority'),
        ],
        default='medium'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ['user', 'package'],
            ['user', 'accommodation'],
            ['user', 'destination'],
        ]
        ordering = ['-created_at']

    def __str__(self):
        if self.package:
            return f"{self.user.username} - {self.package.name}"
        elif self.accommodation:
            return f"{self.user.username} - {self.accommodation.name}"
        elif self.destination:
            return f"{self.user.username} - {self.destination.name}"
        return f"{self.user.username} - Bucket List Item"

    @property
    def item_name(self):
        """Get the name of the bucket list item"""
        if self.package:
            return self.package.name
        elif self.accommodation:
            return self.accommodation.name
        elif self.destination:
            return self.destination.name
        return "Unknown Item"

    @property
    def item_image(self):
        """Get the image of the bucket list item"""
        if self.package:
            return self.package.featured_image
        elif self.accommodation:
            return getattr(self.accommodation, 'image', None)
        elif self.destination:
            return getattr(self.destination, 'image', None)
        return None


class JobApplication(models.Model):
    """Model for job applications submitted through the careers page"""

    POSITION_CHOICES = [
        ('accountant', 'Accountant'),
        ('travel_consultant', 'Travel Consultant'),
        ('graphic_designer', 'Graphic Designer'),
        ('marketing_specialist', 'Marketing Specialist'),
        ('customer_service', 'Customer Service Representative'),
        ('tour_guide', 'Tour Guide'),
        ('operations_manager', 'Operations Manager'),
    ]

    # Personal Information
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(
        max_length=20,
        help_text="Enter your primary contact number (e.g., 254712345678)"
    )
    alternative_phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Enter an alternative contact number (optional)"
    )

    # Position Information
    position_applied_for = models.CharField(max_length=50, choices=POSITION_CHOICES)
    job_listing = models.ForeignKey(
        'JobListing',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Specific job listing if applied through job detail page"
    )
    years_of_experience = models.PositiveIntegerField()
    availability_date = models.DateField()

    # Application Content
    cover_letter = models.TextField(help_text="Tell us why you're interested in this position")
    resume = models.FileField(upload_to='job_applications/resumes/', help_text="Upload your resume (PDF preferred)")

    # System Information
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Email tracking
    admin_notification_sent = models.BooleanField(default=False)
    applicant_confirmation_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Job Application"
        verbose_name_plural = "Job Applications"

    def __str__(self):
        return f"{self.full_name} - {self.get_position_applied_for_display()}"

    def get_position_display(self):
        """Get human-readable position name"""
        return self.get_position_applied_for_display()


class NewsletterSubscription(models.Model):
    """Model for newsletter subscriptions"""

    email = models.EmailField(unique=True, help_text="Subscriber's email address")
    is_active = models.BooleanField(default=True, help_text="Whether the subscription is active")
    is_confirmed = models.BooleanField(default=False, help_text="Whether the email has been confirmed")

    # Subscription preferences
    travel_tips = models.BooleanField(default=True, help_text="Receive travel tips and guides")
    special_offers = models.BooleanField(default=True, help_text="Receive special offers and deals")
    destination_updates = models.BooleanField(default=True, help_text="Receive destination updates")

    # Tracking information
    subscription_date = models.DateTimeField(auto_now_add=True)
    confirmation_date = models.DateTimeField(null=True, blank=True)
    last_email_sent = models.DateTimeField(null=True, blank=True)

    # Email tracking
    confirmation_email_sent = models.BooleanField(default=False)
    admin_notification_sent = models.BooleanField(default=False)

    # Unsubscribe token for secure unsubscribe links
    unsubscribe_token = models.CharField(max_length=64, unique=True, blank=True)

    class Meta:
        ordering = ['-subscription_date']
        verbose_name = "Newsletter Subscription"
        verbose_name_plural = "Newsletter Subscriptions"

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        confirmed = "Confirmed" if self.is_confirmed else "Unconfirmed"
        return f"{self.email} - {status} ({confirmed})"

    def save(self, *args, **kwargs):
        if not self.unsubscribe_token:
            self.unsubscribe_token = self.generate_unsubscribe_token()
        super().save(*args, **kwargs)

    def generate_unsubscribe_token(self):
        """Generate unique unsubscribe token"""
        import secrets
        while True:
            token = secrets.token_urlsafe(32)
            if not NewsletterSubscription.objects.filter(unsubscribe_token=token).exists():
                return token

    def confirm_subscription(self):
        """Confirm the subscription"""
        from django.utils import timezone
        self.is_confirmed = True
        self.confirmation_date = timezone.now()
        self.save()

    def unsubscribe(self):
        """Unsubscribe the user"""
        self.is_active = False
        self.save()


class JobListing(models.Model):
    """Model for job listings on the careers page"""

    JOB_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    ]

    APPLICATION_STATUS_CHOICES = [
        ('open', 'Open'),
        ('reviewing', 'Reviewing Applications'),
        ('closed', 'Closed'),
        ('on_hold', 'On Hold'),
    ]

    # Basic Information
    title = models.CharField(max_length=200, help_text="Job title")
    slug = models.SlugField(max_length=250, unique=True, help_text="URL-friendly version of the title")
    description = models.TextField(help_text="Detailed job description")

    # Job Details
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full_time')
    application_status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='open')
    location = models.CharField(max_length=100, default='Nairobi, Kenya')

    # Requirements and Qualifications
    requirements = models.TextField(help_text="Job requirements and qualifications")
    responsibilities = models.TextField(help_text="Key responsibilities and duties")

    # Optional Information
    salary_range = models.CharField(max_length=100, blank=True, help_text="e.g., 'KES 50,000 - 80,000' or 'Competitive'")
    benefits = models.TextField(blank=True, help_text="Employee benefits and perks")

    # Media
    job_image = models.ImageField(
        upload_to='job_listings/',
        blank=True,
        null=True,
        help_text="Job thumbnail image (recommended: 400x300px)"
    )

    # Dates
    posted_date = models.DateTimeField(auto_now_add=True)
    application_deadline = models.DateField(blank=True, null=True, help_text="Last date to apply")
    updated_at = models.DateTimeField(auto_now=True)

    # SEO and Display
    featured = models.BooleanField(default=False, help_text="Show as featured job")
    is_active = models.BooleanField(default=True, help_text="Display on careers page")

    class Meta:
        ordering = ['-featured', '-posted_date']
        verbose_name = "Job Listing"
        verbose_name_plural = "Job Listings"

    def __str__(self):
        return f"{self.title} - {self.get_job_type_display()}"

    def get_absolute_url(self):
        """Get the URL for this job listing"""
        from django.urls import reverse
        return reverse('users:job_detail', kwargs={'slug': self.slug})

    def is_application_open(self):
        """Check if applications are currently being accepted"""
        if not self.is_active:
            return False
        if self.application_status != 'open':
            return False
        if self.application_deadline:
            from django.utils import timezone
            return timezone.now().date() <= self.application_deadline
        return True

    def get_status_badge_class(self):
        """Get CSS class for status badge"""
        status_classes = {
            'open': 'badge-success',
            'reviewing': 'badge-warning',
            'closed': 'badge-danger',
            'on_hold': 'badge-secondary',
        }
        return status_classes.get(self.application_status, 'badge-secondary')

    def get_type_badge_class(self):
        """Get CSS class for job type badge"""
        type_classes = {
            'full_time': 'badge-primary',
            'part_time': 'badge-info',
            'contract': 'badge-warning',
            'internship': 'badge-success',
        }
        return type_classes.get(self.job_type, 'badge-primary')

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
            # Ensure unique slug
            counter = 1
            original_slug = self.slug
            while JobListing.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)


class QuoteRequest(models.Model):
    """
    Model for quote requests submitted through the website
    """
    # Personal Information
    full_name = models.CharField(max_length=100, help_text="Full name of the person requesting quote")
    email = models.EmailField(help_text="Email address for communication")
    phone_number = models.CharField(max_length=20, help_text="Contact phone number")

    # Travel Details
    destination = models.CharField(max_length=100, help_text="Preferred destination or region")
    preferred_travel_dates = models.CharField(max_length=200, help_text="Preferred travel dates (flexible dates welcome)")
    number_of_travelers = models.PositiveIntegerField(default=1, help_text="Number of people traveling")

    # Package Information (optional - if requesting quote for specific package)
    package = models.ForeignKey(
        "adminside.Package",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Specific package if requesting quote for existing package"
    )

    # Additional Information
    special_requests = CKEditor5Field(
        config_name='default',
        blank=True,
        null=True,
        help_text="Any special requirements, preferences, or additional information"
    )

    # System Information
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the quote request was submitted")
    updated_at = models.DateTimeField(auto_now=True)

    # Email tracking
    confirmation_email_sent = models.BooleanField(default=False, help_text="Whether confirmation email was sent to user")
    admin_notification_sent = models.BooleanField(default=False, help_text="Whether notification was sent to admin")

    # Status tracking
    STATUS_CHOICES = [
        ('new', 'New Request'),
        ('contacted', 'Contacted'),
        ('quoted', 'Quote Sent'),
        ('confirmed', 'Booking Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        help_text="Current status of the quote request"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Quote Request"
        verbose_name_plural = "Quote Requests"

    def __str__(self):
        return f"Quote Request - {self.full_name} ({self.destination})"

    def get_status_badge_class(self):
        """Get CSS class for status badge"""
        status_classes = {
            'new': 'badge-primary',
            'contacted': 'badge-info',
            'quoted': 'badge-warning',
            'confirmed': 'badge-success',
            'cancelled': 'badge-danger',
        }
        return status_classes.get(self.status, 'badge-secondary')


# Signal to create UserProfile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)