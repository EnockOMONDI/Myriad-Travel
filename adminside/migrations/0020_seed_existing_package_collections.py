from django.db import migrations


COLLECTIONS = (
    ('kenya-safaris-and-bush', 'Kenya Safaris & Bush', 'safaris', 'kenya-safari'),
    ('kenya-coast-and-beach', 'Kenya Coast & Beach', 'kenya', 'kenya-coast'),
    ('international-escapes', 'International Escapes', 'world', 'international'),
    ('weekend-hikes-and-day-trips', 'Weekend Hikes & Day Trips', 'kenya', 'day-trips'),
)


def seed_collections(apps, schema_editor):
    TravelCollection = apps.get_model('adminside', 'TravelCollection')
    Package = apps.get_model('adminside', 'Package')

    for slug, name, section, legacy_region in COLLECTIONS:
        collection, _created = TravelCollection.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'section': section,
                'description': f'Packages in the {name} collection.',
                'display_order': 10,
                'is_active': True,
                'show_in_navigation': True,
            },
        )
        package_ids = Package.objects.filter(region=legacy_region).values_list('pk', flat=True)
        collection.packages.add(*package_ids)


def reverse_seed_collections(apps, schema_editor):
    TravelCollection = apps.get_model('adminside', 'TravelCollection')
    TravelCollection.objects.filter(slug__in=[item[0] for item in COLLECTIONS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('adminside', '0019_backfill_package_categories'),
    ]

    operations = [
        migrations.RunPython(seed_collections, reverse_seed_collections),
    ]
