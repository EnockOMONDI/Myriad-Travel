from django.test import TestCase

from adminside.itinerary_audit import analyse_itinerary
from adminside.models import Destination, Itinerary, ItineraryDay, Package, PackageCategory


class ItineraryAuditTests(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(
            name='Audit Coast',
            slug='audit-coast',
            destination_type=Destination.COUNTRY,
            description='Audit destination.',
        )
        self.category = PackageCategory.objects.create(name='Audit Coast', slug='audit-coast')

    def test_embedded_day_range_stays_grouped_without_inventing_days(self):
        package = Package.objects.create(
            name='Audit Beach Escape',
            slug='audit-beach-escape',
            description='Package description.',
            category=self.category,
            main_destination=self.destination,
            duration_days=7,
            duration_nights=6,
            adult_price=50000,
            child_price=25000,
            inclusions='Stay included.',
            exclusions='Flights excluded.',
        )
        itinerary = Itinerary.objects.create(package=package, title='Audit itinerary')
        ItineraryDay.objects.create(
            itinerary=itinerary,
            day_number=1,
            title='Day 1: Arrival - Coast',
            description='Arrival at the hotel. Days 2-6: Leisure by the beach.',
        )
        ItineraryDay.objects.create(
            itinerary=itinerary,
            day_number=2,
            title='Day 7: Departure',
            description='Transfer to the airport.',
        )

        audit = analyse_itinerary(package)

        self.assertEqual(audit['status'], 'needs-review')
        self.assertEqual([row['label'] for row in audit['rows']], ['Day 1', 'Days 2-6', 'Day 7'])
        self.assertEqual(audit['rows'][1]['description'], 'Leisure by the beach.')
