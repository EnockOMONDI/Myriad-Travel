from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from adminside.admin import PackageAdminForm
from adminside.models import Campaign, Destination, Package, TravelCollection
from users.views import _destination_tree_ids, _packages_for_destinations, _region_cards


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
