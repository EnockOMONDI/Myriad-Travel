from django.core.management.base import BaseCommand
from django.utils.text import slugify

from adminside.models import Destination


DESTINATIONS = (
    ('Kilifi', 'kilifi', 'Kilifi coast stays, beaches and dhow-lined shoreline escapes.', 30),
    ('Malindi', 'malindi', 'Malindi beaches, marine experiences and coastal holidays.', 31),
    ('Watamu', 'watamu', 'Watamu beaches, marine conservation and relaxed coastal stays.', 32),
    ('Kisumu', 'kisumu', 'Kisumu on Lake Victoria, with lakeside culture and western Kenya escapes.', 33),
    ('Longonot', 'longonot', 'Mount Longonot day hikes and Rift Valley outdoor escapes.', 34),
    ('Machakos', 'machakos', 'Machakos day trips, hills and short escapes from Nairobi.', 35),
    ('Kajiado / Suswa', 'kajiado-suswa', 'Kajiado and Suswa landscapes for day trips and countryside escapes.', 36),
    ('Sagana', 'sagana', 'Sagana river activities, outdoor adventures and weekend escapes.', 37),
)


class Command(BaseCommand):
    help = 'Create or update Kenya destinations used by the Explore Kenya menu.'

    def handle(self, *args, **options):
        kenya = Destination.objects.filter(
            name='Kenya',
            destination_type=Destination.COUNTRY,
            region='kenya',
        ).first()
        if not kenya:
            self.stderr.write(self.style.ERROR('Kenya country destination was not found.'))
            return

        rows = list(DESTINATIONS)
        if not Destination.objects.filter(slug='lamu').exists():
            rows.append(('Lamu', 'lamu', 'Lamu Island heritage, beaches and island escapes.', 29))

        for name, slug, description, display_order in rows:
            destination, created = Destination.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'destination_type': Destination.PLACE,
                    'region': 'kenya',
                    'parent': kenya,
                    'description': description,
                    'is_active': True,
                    'show_in_navigation': True,
                    'display_order': display_order,
                },
            )
            action = 'created' if created else 'updated'
            self.stdout.write(f'{action}: {destination.name} ({destination.slug})')
