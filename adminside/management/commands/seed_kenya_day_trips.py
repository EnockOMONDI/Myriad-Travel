"""Create the four user-supplied Explore Kenya day trips as unpublished drafts."""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from adminside.models import DayTripDetails, Destination, Itinerary, ItineraryDay, Package, PackageCategory, TravelCollection


TRIPS = [
    {
        'name': 'Nairobi National Park Half-Day Safari', 'slug': 'nairobi-national-park-half-day-safari',
        'destination': ('Nairobi National Park', 'nairobi-national-park', 'nairobi'),
        'departs_from': 'Nairobi', 'duration_label': 'Half day', 'price': 4700,
        'price_basis': 'Based on six guests sharing a safari van',
        'summary': "Start your morning on safari with Nairobi’s skyline in the background. Look out for rhinos, giraffes, zebras and buffaloes as your guide takes you across the park’s open grasslands.",
        'schedule': [
            '6:00 a.m. | Pick up from an agreed location in Nairobi.',
            '6:30–10:00 a.m. | Guided game drive with stops for wildlife viewing and photography.',
            '10:30 a.m. | Return to your Nairobi drop-off point.',
        ],
        'includes': ['Shared return transport in a pop-up-roof safari van', 'Driver-guide', 'Game drive', 'Park entry'],
        'excludes': ['Meals', 'Drinks', 'Tips', 'Personal expenses'],
    },
    {
        'name': 'Mount Longonot Crater Hike', 'slug': 'mount-longonot-crater-hike',
        'destination': ('Mount Longonot', 'mount-longonot', 'kenya'),
        'departs_from': 'Nairobi CBD', 'duration_label': 'Full day', 'price': 3500,
        'price_basis': 'Based on a scheduled shared group departure',
        'summary': 'Hike up Mount Longonot for views into its forested crater and across the Great Rift Valley. Stop at the rim to take in the view or continue around the crater if conditions and the group’s pace allow.',
        'schedule': [
            '6:00 a.m. | Depart from an agreed meeting point in Nairobi CBD.',
            '8:00 a.m. | Arrive at Mount Longonot and begin the guided hike.',
            '10:00 a.m. | Reach the crater rim. Continue around the crater or descend with your guide as arranged.',
            '1:30–2:30 p.m. | Finish the hike and stop for lunch at your own cost.',
            '5:00 p.m. | Arrive back in Nairobi.',
        ],
        'includes': ['Shared return transport from Nairobi CBD', 'Hiking guide', 'Park entry'],
        'excludes': ['Meals', 'Drinking water', 'Hiking gear', 'Tips', 'Personal expenses'],
    },
    {
        'name': 'Wasini Island & Kisite Marine Park Day Trip', 'slug': 'wasini-island-kisite-marine-park-day-trip',
        'destination': ('Wasini Island', 'wasini-island', 'kenya'),
        'departs_from': 'Diani or Ukunda', 'duration_label': 'Full day', 'price': 9500,
        'price_basis': 'Based on six guests sharing transfers from Diani or Ukunda',
        'summary': 'Sail from Shimoni on a traditional dhow, look for dolphins and snorkel over the reefs of Kisite Marine Park when sea conditions allow. After a morning on the water, enjoy a Swahili-style lunch on Wasini Island.',
        'schedule': [
            '7:00 a.m. | Hotel pickup in Diani or Ukunda and transfer to Shimoni.',
            '8:30 a.m. | Board the dhow and cruise towards Kisite Marine Park, looking out for dolphins.',
            '10:00 a.m. | Snorkel and swim at a suitable reef site, subject to sea conditions.',
            '12:30 p.m. | Swahili-style lunch on Wasini Island.',
            '2:30 p.m. | Sail back to Shimoni and transfer to your hotel, arriving around 4:30 p.m.',
        ],
        'includes': ['Shared return hotel transfers', 'Dhow cruise', 'Marine park entry', 'Snorkelling guide and equipment', 'Lunch'],
        'excludes': ['Mombasa transfers', 'Optional village or boardwalk visits', 'Alcoholic drinks', 'Tips', 'Personal expenses'],
    },
    {
        'name': 'Lake Naivasha & Hell’s Gate Day Trip', 'slug': 'lake-naivasha-hells-gate-day-trip',
        'destination': ('Lake Naivasha', 'lake-naivasha', 'kenya'),
        'departs_from': 'Nairobi', 'duration_label': 'Full day', 'price': 5500,
        'price_basis': 'Based on four guests sharing transport',
        'summary': 'Explore the cliffs and open plains of Hell’s Gate, where you can look out for zebras and giraffes. Spend the afternoon by Lake Naivasha or add a boat ride to look for hippos and waterbirds.',
        'schedule': [
            '7:00 a.m. | Depart from an agreed pickup point in Nairobi.',
            '9:30 a.m. | Enter Hell’s Gate National Park and explore by vehicle, with an option to hire a bicycle.',
            '12:30 p.m. | Stop for lunch at your own cost.',
            '2:00 p.m. | Continue to Lake Naivasha for time by the lakeshore or an optional boat ride.',
            '4:00 p.m. | Depart Naivasha and arrive in Nairobi around 6:30 p.m.',
        ],
        'includes': ['Shared return transport from Nairobi', 'Driver-guide', 'Hell’s Gate park entry', 'Bottled water'],
        'excludes': ['Bicycle hire', 'Lunch', 'Lake Naivasha boat ride', 'Crescent Island visit', 'Tips', 'Personal expenses'],
        'extra': 'Optional activities can be quoted when booking.',
    },
]


class Command(BaseCommand):
    help = 'Add four Kenya day trips. Use --publish to make them public immediately.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--publish',
            action='store_true',
            help='Publish the four records and mark their supplied rates confirmed.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        publish = options['publish']
        kenya, _ = Destination.objects.get_or_create(
            slug='kenya',
            defaults={
                'name': 'Kenya',
                'destination_type': Destination.COUNTRY,
                'region': 'kenya',
                'description': 'Kenya',
                'is_active': True,
                'show_in_navigation': True,
            },
        )
        category, _ = PackageCategory.objects.get_or_create(
            slug='day-trips', defaults={'name': 'Day Trips', 'description': 'One-day experiences in Kenya.', 'is_active': True},
        )
        collection, _ = TravelCollection.objects.get_or_create(
            slug='explore-kenya-day-trips',
            defaults={'name': 'Explore Kenya Day Trips', 'section': 'kenya', 'is_active': True, 'show_in_navigation': True},
        )
        for trip in TRIPS:
            name, slug, parent_slug = trip['destination']
            parent = Destination.objects.filter(slug=parent_slug).first() or kenya
            destination, _ = Destination.objects.get_or_create(
                slug=slug,
                defaults={'name': name, 'destination_type': Destination.PLACE, 'parent': parent,
                          'region': 'kenya', 'description': f'{name}, Kenya.', 'is_active': True},
            )
            package, created = Package.objects.get_or_create(
                slug=trip['slug'],
                defaults={
                    'name': trip['name'], 'subtitle': trip['summary'][:280],
                    'description': f"<p>{trip['summary']}</p><p>{trip.get('extra', '')}</p>",
                    'region': 'day-trips', 'category': category, 'main_destination': destination,
                    'duration_days': 1, 'duration_nights': 0, 'adult_price': trip['price'],
                    'child_price': 0,  # Unknown; draft only. Never advertise this as a child fare.
                    'highlights': '\n'.join(trip['includes'][:3]),
                    'inclusions': '<ul>' + ''.join(f'<li>{item}</li>' for item in trip['includes']) + '</ul>',
                    'exclusions': '<ul>' + ''.join(f'<li>{item}</li>' for item in trip['excludes']) + '</ul>',
                    'status': Package.PUBLISHED if publish else Package.DRAFT,
                    'published_at': timezone.now() if publish else None,
                    'is_featured': False, 'lipa_pole_pole': False,
                    'meta_title': trip['name'] + ' | Myriad Travel',
                    'meta_description': trip['summary'][:300],
                },
            )
            if not created:
                collection.packages.add(package)
                if publish:
                    Package.objects.filter(pk=package.pk).update(status=Package.PUBLISHED, published_at=timezone.now())
                    DayTripDetails.objects.filter(package=package).update(price_status='confirmed')
                    self.stdout.write(f'Published existing package: {trip["slug"]}')
                else:
                    self.stdout.write(f'Left existing package unchanged: {trip["slug"]}')
                continue
            collection.packages.add(package)
            DayTripDetails.objects.create(
                package=package, duration_label=trip['duration_label'], departs_from=trip['departs_from'],
                price_basis=trip['price_basis'], schedule='\n'.join(trip['schedule']),
                price_status='confirmed' if publish else 'proposed',
            )
            itinerary = Itinerary.objects.create(package=package, title='Day trip schedule', overview=trip['summary'])
            ItineraryDay.objects.create(itinerary=itinerary, day_number=1, title=trip['name'],
                                        description='\n'.join(trip['schedule']), destination=destination,
                                        lunch=trip['slug'] == 'wasini-island-kisite-marine-park-day-trip')
            label = 'published package' if publish else 'draft'
            self.stdout.write(f'Created {label}: {trip["slug"]}')
