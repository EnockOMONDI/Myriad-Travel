from django.contrib import admin
from django import forms
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import UserBookings, MICEInquiry, StudentTravelInquiry, NGOTravelInquiry, UserProfile, BucketList, Booking, JobApplication, NewsletterSubscription, JobListing, QuoteRequest
from django_ckeditor_5.widgets import CKEditor5Widget

class UserBookingsAdminForm(forms.ModelForm):
    class Meta:
        model = UserBookings
        fields = '__all__'
        widgets = {
            'special_requests': CKEditor5Widget(config_name='default'),
        }

class MICEInquiryAdminForm(forms.ModelForm):
    class Meta:
        model = MICEInquiry
        fields = '__all__'
        widgets = {
            'event_details': CKEditor5Widget(config_name='default'),
        }

class StudentTravelInquiryAdminForm(forms.ModelForm):
    class Meta:
        model = StudentTravelInquiry
        fields = '__all__'
        widgets = {
            'travel_details': CKEditor5Widget(config_name='default'),
        }

class NGOTravelInquiryAdminForm(forms.ModelForm):
    class Meta:
        model = NGOTravelInquiry
        fields = '__all__'
        widgets = {
            'travel_details': CKEditor5Widget(config_name='default'),
        }

@admin.register(UserBookings)
class UserBookingsAdmin(admin.ModelAdmin):
    form = UserBookingsAdminForm
    list_display = ('full_name', 'package', 'user', 'booking_date', 'paid')
    list_filter = ('paid', 'booking_date', 'package')
    search_fields = ('full_name', 'phone_number', 'user__username', 'package__name')
    readonly_fields = ('booking_date',)
    date_hierarchy = 'booking_date'

    fieldsets = (
        ('Booking Information', {
            'fields': ('user', 'package', 'full_name', 'phone_number', 'booking_date')
        }),
        ('Trip Details', {
            'fields': ('number_of_adults', 'number_of_children', 'number_of_rooms',
                      'include_travelling')
        }),
        ('Additional Information', {
            'fields': ('special_requests', 'paid'),
            'classes': ('wide',)
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/ckeditor-admin.css',)
        }
        js = (
            'ckeditor/ckeditor/ckeditor.js',
        )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'package')

@admin.register(MICEInquiry)
class MICEInquiryAdmin(admin.ModelAdmin):
    form = MICEInquiryAdminForm
    list_display = ('company_name', 'contact_person', 'event_type', 'attendees', 'created_at')
    list_filter = ('event_type', 'created_at')
    search_fields = ('company_name', 'contact_person', 'email')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'contact_person', 'email', 'phone_number')
        }),
        ('Event Details', {
            'fields': ('event_type', 'attendees', 'event_details'),
            'classes': ('wide',)
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/ckeditor-admin.css',)
        }
        js = (
            'ckeditor/ckeditor/ckeditor.js',
        )

@admin.register(StudentTravelInquiry)
class StudentTravelInquiryAdmin(admin.ModelAdmin):
    form = StudentTravelInquiryAdminForm
    list_display = ('school_name', 'contact_person', 'program_stage', 'number_of_students', 'created_at')
    list_filter = ('program_stage', 'created_at')
    search_fields = ('school_name', 'contact_person', 'email')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('School Information', {
            'fields': ('school_name', 'contact_person', 'email', 'phone_number')
        }),
        ('Program Details', {
            'fields': ('program_stage', 'number_of_students', 'travel_details'),
            'classes': ('wide',)
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/ckeditor-admin.css',)
        }
        js = (
            'ckeditor/ckeditor/ckeditor.js',
        )

@admin.register(NGOTravelInquiry)
class NGOTravelInquiryAdmin(admin.ModelAdmin):
    form = NGOTravelInquiryAdminForm
    list_display = ('organization_name', 'contact_person', 'travel_purpose', 'number_of_travelers', 'sustainability_requirements', 'created_at')
    list_filter = ('travel_purpose', 'sustainability_requirements', 'created_at')
    search_fields = ('organization_name', 'contact_person', 'email')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Organization Information', {
            'fields': ('organization_name', 'contact_person', 'email', 'phone_number')
        }),
        ('Travel Details', {
            'fields': ('travel_purpose', 'number_of_travelers', 'travel_details', 'sustainability_requirements'),
            'classes': ('wide',)
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    class Media:
        css = {
            'all': ('admin/css/ckeditor-admin.css',)
        }
        js = (
            'ckeditor/ckeditor/ckeditor.js',
        )


# User Profile Admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = (
        'phone_number', 'date_of_birth', 'nationality', 'passport_number',
        'emergency_contact_name', 'emergency_contact_phone',
        'preferred_travel_style', 'dietary_requirements', 'special_needs',
        'email_notifications', 'marketing_emails'
    )


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'full_name', 'package', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at', 'travel_date')
    search_fields = ('booking_reference', 'full_name', 'email', 'package__name')
    readonly_fields = ('booking_reference', 'created_at', 'updated_at')
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_reference', 'package', 'user', 'status')
        }),
        ('Guest Details', {
            'fields': ('full_name', 'email', 'phone_number', 'number_of_adults', 'number_of_children', 'number_of_rooms')
        }),
        ('Travel Details', {
            'fields': ('travel_date', 'selected_accommodations', 'selected_travel_modes')
        }),
        ('Pricing', {
            'fields': ('package_price', 'accommodation_price', 'travel_price', 'total_amount')
        }),
        ('Additional Information', {
            'fields': ('special_requests',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BucketList)
class BucketListAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_type', 'item_name', 'priority', 'created_at')
    list_filter = ('item_type', 'priority', 'created_at')
    search_fields = ('user__username', 'user__email', 'notes')
    readonly_fields = ('created_at',)


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position_applied_for', 'email', 'years_of_experience', 'resume_link', 'created_at')
    list_filter = ('position_applied_for', 'years_of_experience', 'created_at', 'admin_notification_sent', 'applicant_confirmation_sent')
    search_fields = ('full_name', 'email', 'phone_number', 'alternative_phone_number')
    readonly_fields = ('created_at', 'updated_at', 'resume_download_link')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'email', 'phone_number', 'alternative_phone_number')
        }),
        ('Position Details', {
            'fields': ('position_applied_for', 'years_of_experience', 'availability_date')
        }),
        ('Application Content', {
            'fields': ('cover_letter', 'resume', 'resume_download_link'),
            'classes': ('wide',)
        }),
        ('Email Tracking', {
            'fields': ('admin_notification_sent', 'applicant_confirmation_sent'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset for admin list view"""
        return super().get_queryset(request).select_related()

    def resume_link(self, obj):
        """Display resume download link in list view"""
        if obj.resume:
            return format_html(
                '<a href="{}" target="_blank" style="color: #291c1b; font-weight: bold;">'
                '<i class="fas fa-download"></i> Download CV</a>',
                obj.resume.url
            )
        return "No CV uploaded"
    resume_link.short_description = "Resume"
    resume_link.allow_tags = True

    def resume_download_link(self, obj):
        """Display resume download link in detail view"""
        if obj.resume:
            import os
            file_size = ""
            try:
                file_size = f" ({round(obj.resume.size / 1024, 1)} KB)"
            except:
                pass

            return format_html(
                '<div style="margin: 10px 0;">'
                '<a href="{}" target="_blank" class="button" style="background: #291c1b; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; display: inline-block;">'
                '<i class="fas fa-download"></i> Download Resume{}</a>'
                '<br><small style="color: #666; margin-top: 5px; display: block;">File: {}</small>'
                '</div>',
                obj.resume.url,
                file_size,
                os.path.basename(obj.resume.name)
            )
        return format_html('<span style="color: #999;">No resume uploaded</span>')
    resume_download_link.short_description = "Resume Download"
    resume_download_link.allow_tags = True


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'is_confirmed', 'subscription_date', 'get_preferences_summary')
    list_filter = ('is_active', 'is_confirmed', 'travel_tips', 'special_offers', 'destination_updates', 'subscription_date')
    search_fields = ('email',)
    readonly_fields = ('subscription_date', 'confirmation_date', 'last_email_sent', 'unsubscribe_token')
    date_hierarchy = 'subscription_date'
    actions = ['activate_subscriptions', 'deactivate_subscriptions', 'send_confirmation_emails']

    fieldsets = (
        ('Subscription Information', {
            'fields': ('email', 'is_active', 'is_confirmed')
        }),
        ('Preferences', {
            'fields': ('travel_tips', 'special_offers', 'destination_updates'),
            'description': 'Select which types of content the subscriber wants to receive'
        }),
        ('Tracking Information', {
            'fields': ('subscription_date', 'confirmation_date', 'last_email_sent'),
            'classes': ('collapse',)
        }),
        ('Email Tracking', {
            'fields': ('confirmation_email_sent', 'admin_notification_sent'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('unsubscribe_token',),
            'classes': ('collapse',)
        }),
    )

    def get_preferences_summary(self, obj):
        """Display a summary of subscription preferences"""
        preferences = []
        if obj.travel_tips:
            preferences.append('Tips')
        if obj.special_offers:
            preferences.append('Offers')
        if obj.destination_updates:
            preferences.append('Updates')
        return ', '.join(preferences) if preferences else 'None'
    get_preferences_summary.short_description = 'Preferences'

    def activate_subscriptions(self, request, queryset):
        """Bulk activate subscriptions"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subscriptions activated.')
    activate_subscriptions.short_description = 'Activate selected subscriptions'

    def deactivate_subscriptions(self, request, queryset):
        """Bulk deactivate subscriptions"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subscriptions deactivated.')
    deactivate_subscriptions.short_description = 'Deactivate selected subscriptions'

    def send_confirmation_emails(self, request, queryset):
        """Send confirmation emails to unconfirmed subscriptions"""
        from users.views import send_newsletter_subscription_emails
        count = 0
        for subscription in queryset.filter(is_confirmed=False):
            try:
                send_newsletter_subscription_emails(subscription)
                count += 1
            except Exception as e:
                self.message_user(request, f'Error sending email to {subscription.email}: {e}', level='ERROR')

        if count > 0:
            self.message_user(request, f'Confirmation emails sent to {count} subscribers.')
    send_confirmation_emails.short_description = 'Send confirmation emails'


class QuoteRequestAdminForm(forms.ModelForm):
    """Custom form for QuoteRequest admin with CKEditor5 widgets"""
    class Meta:
        model = QuoteRequest
        fields = '__all__'
        widgets = {
            'special_requests': CKEditor5Widget(config_name='default'),
        }


class JobListingAdminForm(forms.ModelForm):
    """Custom form for JobListing admin with CKEditor5 widgets"""
    class Meta:
        model = JobListing
        fields = '__all__'
        widgets = {
            'description': CKEditor5Widget(config_name='default'),
            'requirements': CKEditor5Widget(config_name='default'),
            'responsibilities': CKEditor5Widget(config_name='default'),
            'benefits': CKEditor5Widget(config_name='default'),
        }


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    form = QuoteRequestAdminForm
    list_display = ('full_name', 'email', 'destination', 'number_of_travelers', 'status', 'created_at', 'get_status_badge')
    list_filter = ('status', 'created_at', 'number_of_travelers', 'confirmation_email_sent', 'admin_notification_sent')
    search_fields = ('full_name', 'email', 'phone_number', 'destination')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    actions = ['mark_as_contacted', 'mark_as_quoted', 'mark_as_confirmed', 'mark_as_cancelled']
    list_editable = ('status',)
    list_per_page = 20

    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'email', 'phone_number'),
            'description': 'Customer contact information'
        }),
        ('Travel Details', {
            'fields': ('destination', 'preferred_travel_dates', 'number_of_travelers', 'package'),
            'description': 'Requested travel information'
        }),
        ('Special Requests', {
            'fields': ('special_requests',),
            'classes': ('wide',)
        }),
        ('Status & Tracking', {
            'fields': ('status', 'confirmation_email_sent', 'admin_notification_sent'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset for admin list view"""
        return super().get_queryset(request).select_related('package')

    def get_status_badge(self, obj):
        """Display status with colored badge"""
        status_colors = {
            'new': '#dc3545',
            'contacted': '#ffc107',
            'quoted': '#17a2b8',
            'confirmed': '#28a745',
            'cancelled': '#6c757d',
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'
    get_status_badge.allow_tags = True

    def mark_as_contacted(self, request, queryset):
        """Mark selected quote requests as contacted"""
        updated = queryset.update(status='contacted')
        self.message_user(request, f'{updated} quote requests marked as contacted.')
    mark_as_contacted.short_description = 'Mark as contacted'

    def mark_as_quoted(self, request, queryset):
        """Mark selected quote requests as quoted"""
        updated = queryset.update(status='quoted')
        self.message_user(request, f'{updated} quote requests marked as quoted.')
    mark_as_quoted.short_description = 'Mark as quoted'

    def mark_as_confirmed(self, request, queryset):
        """Mark selected quote requests as confirmed"""
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} quote requests marked as confirmed.')
    mark_as_confirmed.short_description = 'Mark as confirmed'

    def mark_as_cancelled(self, request, queryset):
        """Mark selected quote requests as cancelled"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} quote requests marked as cancelled.')
    mark_as_cancelled.short_description = 'Mark as cancelled'

    class Media:
        css = {
            'all': ('admin/css/ckeditor-admin.css',)
        }
        js = (
            'ckeditor/ckeditor/ckeditor.js',
        )


@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    form = JobListingAdminForm
    list_display = ('title', 'job_type', 'application_status', 'location', 'featured', 'is_active', 'posted_date', 'application_deadline')
    list_filter = ('job_type', 'application_status', 'featured', 'is_active', 'posted_date', 'location')
    search_fields = ('title', 'description', 'requirements', 'location')
    readonly_fields = ('posted_date', 'updated_at', 'slug')
    date_hierarchy = 'posted_date'
    actions = ['mark_as_featured', 'mark_as_not_featured', 'open_applications', 'close_applications']
    list_editable = ('featured', 'is_active', 'application_status')
    list_per_page = 20

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'job_image'),
            'description': 'Basic job information and branding'
        }),
        ('Job Content', {
            'fields': ('description',),
            'description': 'Main job description with rich text formatting',
            'classes': ('wide',)
        }),
        ('Job Details', {
            'fields': ('job_type', 'application_status', 'location', 'salary_range'),
            'description': 'Job classification and compensation details'
        }),
        ('Requirements & Responsibilities', {
            'fields': ('requirements', 'responsibilities'),
            'description': 'Job requirements and key responsibilities with rich text formatting',
            'classes': ('wide',)
        }),
        ('Benefits & Perks', {
            'fields': ('benefits',),
            'description': 'Employee benefits and perks with rich text formatting',
            'classes': ('wide',)
        }),
        ('Dates & Deadlines', {
            'fields': ('application_deadline', 'posted_date', 'updated_at'),
            'description': 'Important dates and deadlines',
            'classes': ('collapse',)
        }),
        ('Display Options', {
            'fields': ('featured', 'is_active'),
            'description': 'Control job visibility and featured status',
            'classes': ('collapse',)
        }),
    )

    def mark_as_featured(self, request, queryset):
        """Mark selected jobs as featured"""
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} jobs marked as featured.')
    mark_as_featured.short_description = 'Mark as featured'

    def mark_as_not_featured(self, request, queryset):
        """Remove featured status from selected jobs"""
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} jobs removed from featured.')
    mark_as_not_featured.short_description = 'Remove featured status'

    def open_applications(self, request, queryset):
        """Open applications for selected jobs"""
        updated = queryset.update(application_status='open', is_active=True)
        self.message_user(request, f'Applications opened for {updated} jobs.')
    open_applications.short_description = 'Open applications'

    def close_applications(self, request, queryset):
        """Close applications for selected jobs"""
        updated = queryset.update(application_status='closed')
        self.message_user(request, f'Applications closed for {updated} jobs.')
    close_applications.short_description = 'Close applications'

    def get_queryset(self, request):
        """Optimize queryset for admin list view"""
        return super().get_queryset(request).select_related()

    class Media:
        css = {
            'all': ('admin/css/ckeditor-admin.css',)
        }
        js = (
            'ckeditor/ckeditor/ckeditor.js',
        )


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)