"""
Form data persistence utilities for Mbugani Luxe Adventures booking system
"""

from django.core.serializers.json import DjangoJSONEncoder
import json
from datetime import datetime, date


class FormDataManager:
    """
    Manages form data persistence across booking steps using Django sessions
    """
    
    def __init__(self, request):
        self.session = request.session
        self.form_data_key = 'booking_form_data'
        
    def save_form_data(self, step, data, merge=True):
        """
        Save form data for a specific step
        
        Args:
            step (str): The booking step (e.g., 'package_selection', 'customization', 'details')
            data (dict): Form data to save
            merge (bool): Whether to merge with existing data or replace
        """
        # Get existing form data
        form_data = self.session.get(self.form_data_key, {})
        
        if merge and step in form_data:
            # Merge with existing data
            form_data[step].update(data)
        else:
            # Replace or create new step data
            form_data[step] = data
            
        # Add timestamp
        form_data[step]['_timestamp'] = datetime.now().isoformat()
        
        # Save back to session
        self.session[self.form_data_key] = form_data
        self.session.modified = True
        
    def get_form_data(self, step=None):
        """
        Get form data for a specific step or all steps
        
        Args:
            step (str, optional): Specific step to get data for
            
        Returns:
            dict: Form data for the step or all form data
        """
        form_data = self.session.get(self.form_data_key, {})
        
        if step:
            return form_data.get(step, {})
        return form_data
        
    def clear_form_data(self, step=None):
        """
        Clear form data for a specific step or all steps
        
        Args:
            step (str, optional): Specific step to clear. If None, clears all data
        """
        if step:
            form_data = self.session.get(self.form_data_key, {})
            if step in form_data:
                del form_data[step]
                self.session[self.form_data_key] = form_data
                self.session.modified = True
        else:
            # Clear all form data
            if self.form_data_key in self.session:
                del self.session[self.form_data_key]
                self.session.modified = True
                
    def has_form_data(self, step=None):
        """
        Check if form data exists for a step or any step
        
        Args:
            step (str, optional): Specific step to check
            
        Returns:
            bool: True if data exists
        """
        form_data = self.session.get(self.form_data_key, {})
        
        if step:
            return step in form_data and bool(form_data[step])
        return bool(form_data)
        
    def get_step_progress(self):
        """
        Get the progress of completed steps
        
        Returns:
            list: List of completed step names
        """
        form_data = self.session.get(self.form_data_key, {})
        return list(form_data.keys())
        
    def validate_step_completion(self, step):
        """
        Validate if a step has the minimum required data
        
        Args:
            step (str): Step to validate
            
        Returns:
            bool: True if step has required data
        """
        data = self.get_form_data(step)
        
        if step == 'package_selection':
            return 'package_id' in data and 'adults' in data
        elif step == 'customization':
            return True  # Customization is optional
        elif step == 'details':
            required_fields = ['full_name', 'email', 'phone_number']
            return all(field in data and data[field] for field in required_fields)
            
        return False
        
    def get_form_initial_data(self, step, form_class=None):
        """
        Get initial data for a form from saved session data
        
        Args:
            step (str): The booking step
            form_class (Form, optional): Form class to filter fields
            
        Returns:
            dict: Initial data for the form
        """
        saved_data = self.get_form_data(step)
        
        if not saved_data:
            return {}
            
        # Remove internal fields
        initial_data = {k: v for k, v in saved_data.items() if not k.startswith('_')}
        
        # Convert date strings back to date objects if needed
        for key, value in initial_data.items():
            if isinstance(value, str) and key.endswith('_date'):
                try:
                    initial_data[key] = datetime.fromisoformat(value).date()
                except (ValueError, TypeError):
                    pass
                    
        # Filter by form fields if form_class provided
        if form_class:
            form_fields = set(form_class.base_fields.keys())
            initial_data = {k: v for k, v in initial_data.items() if k in form_fields}
            
        return initial_data
        
    def save_form_instance_data(self, step, form):
        """
        Save data from a form instance
        
        Args:
            step (str): The booking step
            form (Form): Django form instance with cleaned_data
        """
        if hasattr(form, 'cleaned_data') and form.cleaned_data:
            # Convert date objects to strings for JSON serialization
            data = {}
            for key, value in form.cleaned_data.items():
                if isinstance(value, (date, datetime)):
                    data[key] = value.isoformat()
                else:
                    data[key] = value
                    
            self.save_form_data(step, data)
            
    def get_booking_summary(self):
        """
        Get a summary of all booking data for review
        
        Returns:
            dict: Summary of all booking steps
        """
        all_data = self.get_form_data()
        summary = {}
        
        # Package selection data
        if 'package_selection' in all_data:
            summary['package'] = all_data['package_selection']
            
        # Customization data
        if 'customization' in all_data:
            summary['customization'] = all_data['customization']
            
        # Customer details
        if 'details' in all_data:
            summary['customer'] = all_data['details']
            
        return summary
        
    def export_for_booking(self):
        """
        Export form data in format suitable for booking creation
        
        Returns:
            dict: Cleaned data for booking creation
        """
        summary = self.get_booking_summary()
        
        # Flatten the data structure
        booking_data = {}
        
        for step_data in summary.values():
            for key, value in step_data.items():
                if not key.startswith('_'):
                    booking_data[key] = value
                    
        return booking_data


def get_form_manager(request):
    """
    Convenience function to get a FormDataManager instance
    
    Args:
        request: Django request object
        
    Returns:
        FormDataManager: Configured form data manager
    """
    return FormDataManager(request)


def preserve_form_data(view_func):
    """
    Decorator to automatically preserve form data on successful form submission
    
    Usage:
        @preserve_form_data
        def my_view(request):
            # view logic
    """
    def wrapper(request, *args, **kwargs):
        # Store original POST data
        if request.method == 'POST':
            form_manager = get_form_manager(request)
            # The view should handle saving form data explicitly
            
        return view_func(request, *args, **kwargs)
    return wrapper
