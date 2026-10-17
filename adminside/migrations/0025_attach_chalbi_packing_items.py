from django.db import migrations


def attach_chalbi_packing_items(apps, schema_editor):
    Package = apps.get_model('adminside', 'Package')
    PackingListItem = apps.get_model('adminside', 'PackingListItem')
    package = Package.objects.filter(slug='twende-chalbi-4-nights-5-days').first()
    if not package:
        return
    items = PackingListItem.objects.filter(is_active=True, name__in=[
        'Closed shoes', 'Hat or cap', 'Sunglasses', 'Sunscreen', 'Warm jacket',
        'Comfortable clothing', 'Swimwear and towel', 'Refillable water bottle',
        'Power bank', 'Toiletries', 'Identification document', 'Kenyan cash',
    ])
    package.packing_items.set(items)


class Migration(migrations.Migration):
    dependencies = [('adminside', '0024_seed_package_content_and_chalbi')]
    operations = [migrations.RunPython(attach_chalbi_packing_items, migrations.RunPython.noop)]
