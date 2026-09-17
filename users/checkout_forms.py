"""
Checkout forms for Mbugani Luxe Adventures
"""

from django import forms
from django.core.validators import RegexValidator
from django_ckeditor_5.widgets import CKEditor5Widget


class CheckoutForm(forms.Form):
    """
    Guest checkout form for collecting customer information
    """
    
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your full name',
            'required': True
        }),
        label='Full Name'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your email address',
            'required': True
        }),
        label='Email Address'
    )
    
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    phone_number = forms.CharField(
        validators=[phone_validator],
        max_length=17,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '+254 700 000 000',
            'required': True
        }),
        label='Phone Number'
    )
    
    travel_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-lg',
            'type': 'date',
            'placeholder': 'Select travel date'
        }),
        label='Preferred Travel Date (Optional)'
    )
    
    special_requests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Any special requests, dietary requirements, or additional information...'
        }),
        label='Special Requests (Optional)'
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='I accept the terms and conditions'
    )
    
    marketing_consent = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='I would like to receive travel updates and special offers from Mbugani Luxe Adventures'
    )

    def clean_full_name(self):
        """
        Validate full name
        """
        full_name = self.cleaned_data['full_name']
        if len(full_name.split()) < 2:
            raise forms.ValidationError('Please enter your full name (first and last name).')
        return full_name

    def clean_email(self):
        """
        Validate email format
        """
        email = self.cleaned_data['email']
        return email.lower()


class TravelerDetailsForm(forms.Form):
    """
    Form for collecting traveler count and room requirements
    """
    
    adults = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'min': '1',
            'max': '20'
        }),
        label='Adults (18+ years)'
    )
    
    children = forms.IntegerField(
        min_value=0,
        max_value=20,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'min': '0',
            'max': '20'
        }),
        label='Children (0-17 years)'
    )
    
    rooms = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'min': '1',
            'max': '10'
        }),
        label='Rooms Required'
    )

    def clean(self):
        """
        Validate traveler details
        """
        cleaned_data = super().clean()
        adults = cleaned_data.get('adults', 0)
        children = cleaned_data.get('children', 0)
        rooms = cleaned_data.get('rooms', 0)
        
        total_travelers = adults + children
        
        if total_travelers == 0:
            raise forms.ValidationError('At least one traveler is required.')
        
        if rooms > total_travelers:
            raise forms.ValidationError('Number of rooms cannot exceed number of travelers.')
        
        return cleaned_data


class AccommodationSelectionForm(forms.Form):
    """
    Form for selecting accommodations
    """
    
    def __init__(self, *args, **kwargs):
        accommodations = kwargs.pop('accommodations', [])
        super().__init__(*args, **kwargs)
        
        for accommodation in accommodations:
            self.fields[f'accommodation_{accommodation.id}'] = forms.BooleanField(
                required=False,
                label=accommodation.name,
                widget=forms.CheckboxInput(attrs={
                    'class': 'form-check-input accommodation-checkbox',
                    'data-price': accommodation.price_per_room_per_night,
                    'data-accommodation-id': accommodation.id
                })
            )


class TravelModeSelectionForm(forms.Form):
    """
    Form for selecting travel modes
    """
    
    def __init__(self, *args, **kwargs):
        travel_modes = kwargs.pop('travel_modes', [])
        super().__init__(*args, **kwargs)
        
        for travel_mode in travel_modes:
            self.fields[f'travel_mode_{travel_mode.id}'] = forms.BooleanField(
                required=False,
                label=travel_mode.name,
                widget=forms.CheckboxInput(attrs={
                    'class': 'form-check-input travel-mode-checkbox',
                    'data-price': travel_mode.price_per_person,
                    'data-travel-mode-id': travel_mode.id
                })
            )
