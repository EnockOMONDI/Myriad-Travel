from datetime import time, timedelta
from pathlib import Path

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from adminside.admin import PackageAdminForm
from adminside.package_wizard import DestinationQuickCreateForm, PackageContentForm, PackageOptionsForm
from adminside.models import Accommodation, Campaign, Destination, Package, PackingListItem, TravelCollection, TravelMode
from users.views import _destination_ids_for_page, _destination_tree_ids, _packages_for_destinations, _region_cards


class PackageFlowTests(TestCase):
    def setUp(self):
        self.country = Destination.objects.create(
            name='Kenya', slug='kenya', destination_type=Destination.COUNTRY,
            region='kenya', description='Kenya', is_active=True,
        )
        self.destination = Destination.objects.create(
            name='Maasai Mara', slug='maasai-mara', destination_type=Destination.PLACE,
            parent=self.country, region='kenya', description='Mara', is_active=True,
        )
        self.child = Destination.objects.create(
            name='Mara Triangle', slug='mara-triangle', destination_type=Destination.PLACE,
            parent=self.destination, region='kenya', description='Triangle', is_active=True,
        )
        self.package = Package.objects.create(
            name='Mara Safari', slug='mara-safari', description='Safari',
            main_destination=self.child, duration_days=3, duration_nights=2,
            adult_price=50000, child_price=30000, status=Package.PUBLISHED,
        )

    def test_destination_tree_includes_descendants_and_inherited_packages(self):
        ids = _destination_tree_ids(self.country)
        self.assertEqual(set(ids), {self.country.id, self.destination.id, self.child.id})
        self.assertEqual(list(_packages_for_destinations(ids)), [self.package])

    def test_country_page_includes_linked_multi_country_group_packages(self):
        group = Destination.objects.create(
            name='Indian Ocean Circuit', slug='indian-ocean-circuit',
            destination_type=Destination.COUNTRY, region='africa',
            description='A multi-country travel area.', is_active=True,
            is_multi_country=True,
        )
        group.member_countries.add(self.country)
        group_package = Package.objects.create(
            name='Kenya and Indian Ocean Circuit', slug='kenya-indian-ocean-circuit',
            description='A multi-country journey.', main_destination=group,
            duration_days=8, duration_nights=7, adult_price=120000,
            child_price=80000, status=Package.PUBLISHED,
        )

        ids = _destination_ids_for_page(self.country)

        self.assertIn(group.id, ids)
        self.assertIn(group_package, _packages_for_destinations(ids))

    def test_homepage_region_cards_include_existing_kenya_records_in_africa(self):
        africa = next(card for card in _region_cards() if card['slug'] == 'africa')
        self.assertEqual(africa['destination_count'], 1)
        self.assertEqual(africa['package_count'], 1)

    def test_package_admin_exposes_existing_collections_as_multi_select(self):
        first = TravelCollection.objects.create(name='Kenya Safaris', slug='kenya-safaris', section='safaris')
        second = TravelCollection.objects.create(name='Weekend Trips', slug='weekend-trips', section='safaris')
        first.packages.add(self.package)
        form = PackageAdminForm(instance=self.package)
        self.assertIn('Collections', form.fields['travel_collections'].label)
        self.assertEqual(set(form.fields['travel_collections'].initial), {first})
        self.assertIn(second, form.fields['travel_collections'].queryset)

    def test_package_pricing_and_packing_are_database_driven(self):
        self.package.single_occupancy_supplement = 5000
        self.package.packing_list_custom = 'Refillable bottle, Power bank'
        self.package.save()
        item, _ = PackingListItem.objects.get_or_create(name='Closed shoes')
        self.package.packing_items.add(item)

        self.package.refresh_from_db()
        self.assertTrue(self.package.has_single_occupancy)
        self.assertEqual(self.package.single_occupancy_price, 55000)
        self.assertEqual(self.package.packing_list(), ['Closed shoes', 'Refillable bottle', 'Power bank'])

    def test_admin_explains_optional_single_supplement_and_metadata(self):
        form = PackageAdminForm(instance=self.package)
        self.assertIn('supplement', form.fields['single_occupancy_supplement'].help_text.lower())
        self.assertIn('comma-separated', form.fields['meta_keywords'].help_text.lower())
        self.assertIn('concise answer', form.fields['aeo_summary'].help_text.lower())

    def test_add_package_wizard_exposes_complete_content_and_search_fields(self):
        content = PackageContentForm()
        options = PackageOptionsForm()
        for field in ('price_currency', 'adult_price', 'child_price', 'single_occupancy_supplement', 'travel_notes', 'packing_items', 'packing_list_custom'):
            self.assertIn(field, content.fields)
        for field in ('meta_title', 'meta_description', 'meta_keywords', 'aeo_summary'):
            self.assertIn(field, options.fields)
        self.assertIn('comma-separated', options.fields['meta_keywords'].help_text.lower())
        self.assertIn('one concise sentence', options.fields['aeo_summary'].help_text.lower())

    def test_chalbi_template_has_no_stale_price_fallback_or_view_override(self):
        root = Path(__file__).resolve().parents[2]
        view_source = (root / 'users' / 'views.py').read_text()
        template_source = (root / 'users' / 'templates' / 'users' / 'pages' / 'package_detail_chalbi.html').read_text()
        self.assertNotIn('CHALBI_SPECIAL_OFFER', view_source)
        self.assertNotIn('CHALBI_DAY_META', view_source)
        self.assertNotIn('default:58000', template_source)

    def test_campaign_public_status_supports_new_closing_and_scheduled(self):
        package = self.package
        today = timezone.localdate()
        scheduled = Campaign.objects.create(title='Christmas', package=package, starts_on=today + timedelta(days=10), ends_on=today + timedelta(days=20))
        new = Campaign.objects.create(title='New', package=package, starts_on=today, ends_on=today + timedelta(days=20))
        closing = Campaign.objects.create(title='Closing', package=package, starts_on=today - timedelta(days=10), ends_on=today + timedelta(days=3))
        self.assertEqual(scheduled.public_status, 'Scheduled')
        self.assertEqual(new.public_status, 'New')
        self.assertEqual(closing.public_status, 'Closing soon')

    def test_admin_guide_requires_login_and_explains_nakuru_flow(self):
        self.assertEqual(self.client.get('/adminside/how-it-works/').status_code, 302)
        self.assertEqual(reverse('adminside:how_it_works'), '/adminside/how-it-works/')

    def test_package_wizard_saves_accommodation_and_travel_options(self):
        accommodation = Accommodation.objects.create(
            name='Mara Camp', slug='mara-camp', description='Camp',
            destination=self.destination, price_per_room_per_night=12000,
            amenities='Meals',
        )
        travel_mode = TravelMode.objects.create(
            name='Safari Cruiser', transport_type=TravelMode.CRUISER,
            departure_location='Nairobi', arrival_location='Maasai Mara',
            departure_time=time(7, 0), arrival_time=time(13, 0),
            duration_minutes=360, price_per_person=10000,
        )
        user = User.objects.create_user(
            username='wizard-admin', password='password123', is_staff=True,
        )
        self.client.force_login(user)

        response = self.client.post(reverse('adminside:package_wizard'), {
            'step': 1, 'name': 'Mara Guided Escape', 'subtitle': 'A clear safari plan.',
            'main_destination': self.destination.id, 'duration_days': 4, 'duration_nights': 3,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('adminside:package_wizard') + '?step=2')
        self.client.post(reverse('adminside:package_wizard'), {
            'step': 2, 'legacy_collection': 'kenya-safari',
        })
        self.client.post(reverse('adminside:package_wizard'), {
            'step': 3, 'description': 'A practical safari for travellers.',
            'highlights': 'Game drives', 'inclusions': 'Transport', 'exclusions': 'Personal costs',
            'price_currency': 'KES', 'adult_price': 70000, 'child_price': 45000,
            'single_occupancy_supplement': 12000, 'travel_notes': 'Early starts',
            'packing_list_custom': 'Sun hat, Power bank',
        })
        response = self.client.post(reverse('adminside:package_wizard'), {
            'step': 4, 'available_accommodations': [accommodation.id],
            'available_travel_modes': [travel_mode.id],
            'status': Package.DRAFT, 'home_rank': 100,
        })
        self.assertEqual(response.status_code, 302)
        created = Package.objects.get(name='Mara Guided Escape')
        self.assertEqual(created.main_destination, self.destination)
        self.assertEqual(created.region, 'kenya-safari')
        self.assertEqual(created.adult_price, 70000)
        self.assertEqual(created.single_occupancy_supplement, 12000)
        self.assertEqual(created.travel_notes, 'Early starts')
        self.assertEqual(created.packing_list_custom, 'Sun hat, Power bank')
        self.assertEqual(list(created.available_accommodations.all()), [accommodation])
        self.assertEqual(list(created.available_travel_modes.all()), [travel_mode])

    def test_package_wizard_can_create_and_select_missing_destination(self):
        user = User.objects.create_user(
            username='destination-admin', password='password123', is_staff=True,
        )
        self.client.force_login(user)

        invalid_form = DestinationQuickCreateForm(data={
            'step': 1,
            'action': 'create_destination',
            'name': 'Lake Nakuru National Park',
            'destination_type': Destination.PLACE,
            'region': 'kenya',
            'parent': self.destination.id,
            'description': 'A wildlife destination in the Rift Valley.',
        })
        self.assertFalse(invalid_form.is_valid())
        self.assertIn('A specific place must belong to an existing country or city.', invalid_form.errors['parent'])
        self.assertFalse(Destination.objects.filter(name='Lake Nakuru National Park').exists())

        nakuru = Destination.objects.create(
            name='Nakuru', slug='nakuru', destination_type=Destination.CITY,
            parent=self.country, region='kenya', description='Nakuru', is_active=True,
        )
        response = self.client.post(reverse('adminside:package_wizard'), {
            'step': 1,
            'action': 'create_destination',
            'name': 'Lake Nakuru National Park',
            'destination_type': Destination.PLACE,
            'region': 'kenya',
            'parent': nakuru.id,
            'description': 'A wildlife destination in the Rift Valley.',
        })

        created = Destination.objects.get(name='Lake Nakuru National Park')
        self.assertEqual(response.status_code, 302)
        self.assertIn(f'destination_id={created.id}', response['Location'])

    def test_travel_type_choices_include_client_facing_options(self):
        choices = dict(TravelMode.TRANSPORT_TYPES)

        self.assertEqual(choices[TravelMode.FLIGHT], 'Flight')
        self.assertEqual(choices[TravelMode.CHARTER_FLIGHT], 'Charter Flight')
        self.assertEqual(choices[TravelMode.CAR], 'Vehicle / Car')
        self.assertEqual(choices[TravelMode.BOAT], 'Boat / Ferry')
        self.assertEqual(choices[TravelMode.TRAIN], 'Train')
        self.assertEqual(choices[TravelMode.TOUR_VAN], 'Tour Van')
        self.assertEqual(choices[TravelMode.CRUISE_SHIP], 'Cruise Ship')
        self.assertEqual(choices[TravelMode.CRUISER], '4x4 Cruiser')
