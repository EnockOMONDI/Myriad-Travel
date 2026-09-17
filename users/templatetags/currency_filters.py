"""
Currency formatting template filters for Mbugani Luxe Adventures
"""

from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def currency_format(value):
    """
    Format a number as currency with $ symbol and proper formatting
    """
    try:
        if value is None:
            return "$0"
        
        # Convert to Decimal for precise formatting
        if isinstance(value, str):
            value = Decimal(value)
        elif not isinstance(value, Decimal):
            value = Decimal(str(value))
        
        # Format with commas and 2 decimal places if needed
        if value % 1 == 0:
            # No decimal places for whole numbers
            return f"${value:,.0f}"
        else:
            # 2 decimal places for non-whole numbers
            return f"${value:,.2f}"
            
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return "$0"


@register.filter
def mul(value, arg):
    """
    Multiply two values - useful for template calculations
    """
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return 0


@register.filter
def add_currency(value, arg):
    """
    Add two currency values
    """
    try:
        return Decimal(str(value)) + Decimal(str(arg))
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return 0


@register.filter
def subtract_currency(value, arg):
    """
    Subtract two currency values
    """
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return 0
