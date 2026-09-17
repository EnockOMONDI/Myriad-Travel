"""
Session-based cart system for Mbugani Luxe Adventures
"""

from decimal import Decimal
from django.conf import settings
from adminside.models import Package, Accommodation, TravelMode
from .models import GuestBooking


class Cart:
    """
    Session-based cart for guest users
    """
    
    def __init__(self, request):
        """
        Initialize the cart
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        self.session_key = request.session.session_key
        if not self.session_key:
            request.session.create()
            self.session_key = request.session.session_key

    def add_package(self, package, adults=1, children=0, rooms=1, override_quantity=False):
        """
        Add a package to the cart or update its quantity
        """
        package_id = str(package.id)
        if package_id not in self.cart:
            self.cart[package_id] = {
                'adults': 0,
                'children': 0,
                'rooms': 0,
                'accommodations': [],
                'travel_modes': [],
                'custom_accommodation': '',
                'self_drive': False,
                'price': str(package.adult_price)
            }
        
        if override_quantity:
            self.cart[package_id]['adults'] = adults
            self.cart[package_id]['children'] = children
            self.cart[package_id]['rooms'] = rooms
        else:
            self.cart[package_id]['adults'] += adults
            self.cart[package_id]['children'] += children
            self.cart[package_id]['rooms'] += rooms
        
        self.save()

    def add_accommodation(self, package_id, accommodation_id):
        """
        Add accommodation to a package in cart
        """
        package_id = str(package_id)
        if package_id in self.cart:
            if accommodation_id not in self.cart[package_id]['accommodations']:
                self.cart[package_id]['accommodations'].append(accommodation_id)
                self.save()

    def remove_accommodation(self, package_id, accommodation_id):
        """
        Remove accommodation from a package in cart
        """
        package_id = str(package_id)
        if package_id in self.cart:
            if accommodation_id in self.cart[package_id]['accommodations']:
                self.cart[package_id]['accommodations'].remove(accommodation_id)
                self.save()

    def add_travel_mode(self, package_id, travel_mode_id):
        """
        Add travel mode to a package in cart
        """
        package_id = str(package_id)
        if package_id in self.cart:
            if travel_mode_id not in self.cart[package_id]['travel_modes']:
                self.cart[package_id]['travel_modes'].append(travel_mode_id)
                self.save()

    def remove_travel_mode(self, package_id, travel_mode_id):
        """
        Remove travel mode from a package in cart
        """
        package_id = str(package_id)
        if package_id in self.cart:
            if travel_mode_id in self.cart[package_id]['travel_modes']:
                self.cart[package_id]['travel_modes'].remove(travel_mode_id)
                self.save()

    def set_custom_accommodation(self, package_id, custom_text):
        """
        Set custom accommodation text for a package in cart
        """
        package_id = str(package_id)
        if package_id in self.cart:
            self.cart[package_id]['custom_accommodation'] = custom_text
            self.save()

    def set_self_drive(self, package_id, is_self_drive):
        """
        Set self-drive option for a package in cart
        """
        package_id = str(package_id)
        if package_id in self.cart:
            self.cart[package_id]['self_drive'] = is_self_drive
            self.save()

    def remove_package(self, package_id):
        """
        Remove a package from the cart
        """
        package_id = str(package_id)
        if package_id in self.cart:
            del self.cart[package_id]
            self.save()

    def save(self):
        """
        Mark the session as modified to make sure it gets saved
        """
        self.session.modified = True

    def clear(self):
        """
        Remove cart from session
        """
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True

    def get_total_price(self):
        """
        Calculate total price for all items in cart
        """
        total = Decimal('0')
        for package_id, item in self.cart.items():
            try:
                package = Package.objects.get(id=package_id)
                
                # Package base price
                package_total = Decimal(str(package.adult_price)) * item['adults']
                
                # Add children pricing (70% of adult price)
                if item['children'] > 0:
                    child_price = Decimal(str(package.adult_price)) * Decimal('0.7')
                    package_total += child_price * item['children']
                
                # Add accommodation costs
                for acc_id in item['accommodations']:
                    try:
                        accommodation = Accommodation.objects.get(id=acc_id)
                        package_total += Decimal(str(accommodation.price_per_room_per_night)) * item['rooms'] * package.duration_days
                    except Accommodation.DoesNotExist:
                        continue
                
                # Add travel costs (skip if self-drive is selected)
                if not item.get('self_drive', False):
                    for travel_id in item['travel_modes']:
                        try:
                            travel_mode = TravelMode.objects.get(id=travel_id)
                            package_total += Decimal(str(travel_mode.price_per_person)) * (item['adults'] + item['children'])
                        except TravelMode.DoesNotExist:
                            continue
                
                total += package_total
                
            except Package.DoesNotExist:
                continue
        
        return total

    def get_cart_items(self):
        """
        Get detailed cart items with package objects
        """
        items = []
        for package_id, item in self.cart.items():
            try:
                package = Package.objects.get(id=package_id)
                
                # Get accommodation objects
                accommodations = []
                for acc_id in item['accommodations']:
                    try:
                        accommodations.append(Accommodation.objects.get(id=acc_id))
                    except Accommodation.DoesNotExist:
                        continue
                
                # Get travel mode objects
                travel_modes = []
                for travel_id in item['travel_modes']:
                    try:
                        travel_modes.append(TravelMode.objects.get(id=travel_id))
                    except TravelMode.DoesNotExist:
                        continue
                
                # Calculate item total
                item_total = Decimal(str(package.adult_price)) * item['adults']
                if item['children'] > 0:
                    child_price = Decimal(str(package.adult_price)) * Decimal('0.7')
                    item_total += child_price * item['children']

                for accommodation in accommodations:
                    item_total += Decimal(str(accommodation.price_per_room_per_night)) * item['rooms'] * package.duration_days

                # Add travel costs only if not self-drive
                if not item.get('self_drive', False):
                    for travel_mode in travel_modes:
                        item_total += Decimal(str(travel_mode.price_per_person)) * (item['adults'] + item['children'])
                
                items.append({
                    'package': package,
                    'adults': item['adults'],
                    'children': item['children'],
                    'rooms': item['rooms'],
                    'accommodations': accommodations,
                    'travel_modes': travel_modes,
                    'custom_accommodation': item.get('custom_accommodation', ''),
                    'self_drive': item.get('self_drive', False),
                    'total_price': item_total
                })
                
            except Package.DoesNotExist:
                continue
        
        return items

    def __len__(self):
        """
        Count all items in the cart
        """
        return sum(item['adults'] + item['children'] for item in self.cart.values())

    def __iter__(self):
        """
        Iterate over the items in the cart and get the packages from the database
        """
        package_ids = self.cart.keys()
        packages = Package.objects.filter(id__in=package_ids)
        cart = self.cart.copy()
        
        for package in packages:
            cart[str(package.id)]['package'] = package
        
        for item in cart.values():
            yield item
