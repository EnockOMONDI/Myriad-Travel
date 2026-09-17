
from django.contrib.auth.forms import UserCreationForm
from .models import UserBookings
from django import forms
from django.contrib.auth.models import User
from .models import MICEInquiry, StudentTravelInquiry, NGOTravelInquiry, JobApplication, NewsletterSubscription, NewsletterSubscription, QuoteRequest
import re


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'input-box'}), label='')
    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'First Name', 'class': 'input-box'}), label='')
    last_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Last Name', 'class': 'input-box'}), label='')
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Email', 'class': 'input-box'}), label='')
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'input-box'}), label='')
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password', 'class': 'input-box'}), label='')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email',)

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        return email






class UserBookingsForm(forms.ModelForm):
    class Meta:
        model = UserBookings
        fields = [
            'full_name',
            'phone_number',
            'number_of_adults',
            'number_of_children',
            'number_of_rooms',
            'include_travelling',
            'special_requests',
            'paid'
        ]



class MICEInquiryForm(forms.ModelForm):
    class Meta:
        model = MICEInquiry
        fields = ['company_name', 'contact_person', 'email', 'phone_number',
                 'event_type', 'attendees', 'event_details']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes and placeholders to form fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.replace('_', ' ').title()
            })


class StudentTravelInquiryForm(forms.ModelForm):
    class Meta:
        model = StudentTravelInquiry
        fields = ['school_name', 'contact_person', 'email', 'phone_number',
                 'program_stage', 'number_of_students', 'travel_details']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes and placeholders to form fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.replace('_', ' ').title()
            })


class NGOTravelInquiryForm(forms.ModelForm):
    class Meta:
        model = NGOTravelInquiry
        fields = ['organization_name', 'contact_person', 'email', 'phone_number',
                 'organization_type', 'travel_purpose', 'number_of_travelers',
                 'travel_details', 'sustainability_requirements']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add classes and placeholders to form fields
        for field in self.fields:
            if field == 'sustainability_requirements':
                self.fields[field].widget.attrs.update({
                    'class': 'form-check-input'
                })
            else:
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': field.replace('_', ' ').title()
                })


class JobApplicationForm(forms.ModelForm):
    """Form for job applications on the careers page"""

    class Meta:
        model = JobApplication
        fields = [
            'full_name', 'email', 'phone_number', 'alternative_phone_number', 'position_applied_for',
            'years_of_experience', 'availability_date', 'cover_letter', 'resume'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your primary contact number (e.g., 254712345678)'
            }),
            'alternative_phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter an alternative contact number (optional)'
            }),
            'position_applied_for': forms.Select(attrs={
                'class': 'form-control'
            }),
            'years_of_experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Years of experience',
                'min': '0',
                'max': '50'
            }),
            'availability_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'cover_letter': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Tell us why you\'re interested in this position and what makes you a great fit...',
                'rows': 6
            }),
            'resume': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            })
        }

    def clean_phone_number(self):
        """Validate primary phone number format"""
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Remove spaces, hyphens, and parentheses
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone_number)

            # Check if it contains only digits and optional + at the beginning
            if not re.match(r'^\+?[0-9]{10,15}$', cleaned_phone):
                raise forms.ValidationError(
                    "Please enter a valid phone number (10-15 digits, optionally starting with +)"
                )

            return phone_number
        return phone_number

    def clean_alternative_phone_number(self):
        """Validate alternative phone number format (optional)"""
        alt_phone = self.cleaned_data.get('alternative_phone_number')
        if alt_phone:
            # Remove spaces, hyphens, and parentheses
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', alt_phone)

            # Check if it contains only digits and optional + at the beginning
            if not re.match(r'^\+?[0-9]{10,15}$', cleaned_phone):
                raise forms.ValidationError(
                    "Please enter a valid phone number (10-15 digits, optionally starting with +)"
                )

            return alt_phone
        return alt_phone

    def clean_resume(self):
        """Validate resume file upload"""
        resume = self.cleaned_data.get('resume')
        if resume:
            # Check file size (max 5MB)
            if resume.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Resume file size must be less than 5MB.')

            # Check file extension
            allowed_extensions = ['.pdf', '.doc', '.docx']
            file_extension = resume.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError('Resume must be a PDF, DOC, or DOCX file.')

        return resume

    def clean_email(self):
        """Validate email format"""
        email = self.cleaned_data.get('email')
        if email:
            # Basic email validation (Django already does this, but we can add custom logic)
            if not '@' in email or not '.' in email.split('@')[-1]:
                raise forms.ValidationError('Please enter a valid email address.')
        return email


class QuoteRequestForm(forms.ModelForm):
    """Form for quote requests submitted through the website"""

    class Meta:
        model = QuoteRequest
        fields = [
            'full_name', 'email', 'phone_number', 'destination',
            'preferred_travel_dates', 'number_of_travelers', 'special_requests'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your full name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address',
                'required': True
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your contact number (e.g., +254712345678)',
                'required': True
            }),
            'destination': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Preferred destination or region',
                'required': True
            }),
            'preferred_travel_dates': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Preferred travel dates (flexible dates welcome)',
                'required': True
            }),
            'number_of_travelers': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of travelers',
                'min': '1',
                'max': '50',
                'required': True
            }),
            'special_requests': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Any special requirements, preferences, or additional information...',
                'rows': 4
            })
        }

    def clean_phone_number(self):
        """Validate phone number format"""
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Remove spaces, hyphens, and parentheses
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone_number)

            # Check if it contains only digits and optional + at the beginning
            if not re.match(r'^\+?[0-9]{10,15}$', cleaned_phone):
                raise forms.ValidationError(
                    "Please enter a valid phone number (10-15 digits, optionally starting with +)"
                )

            return phone_number
        return phone_number

    def clean_email(self):
        """Validate email format"""
        email = self.cleaned_data.get('email')
        if email:
            # Basic email validation (Django already does this, but we can add custom logic)
            if not '@' in email or not '.' in email.split('@')[-1]:
                raise forms.ValidationError('Please enter a valid email address.')
        return email

    def clean_number_of_travelers(self):
        """Validate number of travelers"""
        num_travelers = self.cleaned_data.get('number_of_travelers')
        if num_travelers and (num_travelers < 1 or num_travelers > 50):
            raise forms.ValidationError('Number of travelers must be between 1 and 50.')
        return num_travelers


class NewsletterSubscriptionForm(forms.ModelForm):
    """Form for newsletter subscriptions"""

    class Meta:
        model = NewsletterSubscription
        fields = ['email', 'travel_tips', 'special_offers', 'destination_updates']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form_control',
                'placeholder': 'Enter your email address',
                'required': True
            }),
            'travel_tips': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'special_offers': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'destination_updates': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_email(self):
        """Validate email and check for existing subscriptions"""
        email = self.cleaned_data.get('email')
        if email:
            # Check if email is already subscribed and active
            existing_subscription = NewsletterSubscription.objects.filter(
                email=email,
                is_active=True
            ).first()

            if existing_subscription:
                raise forms.ValidationError('This email is already subscribed to our newsletter.')

        return email


class NewsletterSubscriptionSimpleForm(forms.Form):
    """Simple form for footer newsletter subscription"""

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form_control',
            'placeholder': 'Email Address',
            'required': True
        })
    )

    def clean_email(self):
        """Validate email and check for existing subscriptions"""
        email = self.cleaned_data.get('email')
        if email:
            # Check if email is already subscribed and active
            existing_subscription = NewsletterSubscription.objects.filter(
                email=email,
                is_active=True
            ).first()

            if existing_subscription:
                raise forms.ValidationError('This email is already subscribed to our newsletter.')

        return email