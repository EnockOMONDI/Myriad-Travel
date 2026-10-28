from django.core.management.base import BaseCommand
from django.utils.text import slugify

from adminside.models import PackageCategory


CATEGORIES = (
    ('Wildlife Safaris', 'Classic game drives, Big Five and migration experiences'),
    ('Adventure Safaris', 'Hiking, trekking, camping and off-the-beaten-path experiences'),
    ('Luxury Safaris', 'Exclusive lodges, private safaris and fly-in experiences'),
    ('Cultural Safaris', 'Authentic cultural and community experiences'),
    ('Photography & Birding Safaris', 'Special-interest safaris for photographers and bird enthusiasts'),
    ('Honeymoon Safaris', 'Romantic bush escapes and private experiences'),
    ('Family Safaris', 'Family-friendly itineraries and experiences'),
    ('Group Joining Safaris', 'Scheduled shared departures and affordable safari packages'),
)


class Command(BaseCommand):
    help = 'Create or update the eight Tours & Safaris menu categories.'

    def handle(self, *args, **options):
        for display_order, (name, description) in enumerate(CATEGORIES, start=1):
            slug = slugify(name)
            category, created = PackageCategory.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'description': description,
                    'display_order': display_order,
                    'is_active': True,
                    'show_in_navigation': True,
                },
            )
            action = 'created' if created else 'updated'
            self.stdout.write(f'{action}: {category.name} ({category.slug})')
