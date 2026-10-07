from django.db import migrations


def copy_primary_category_to_categories(apps, schema_editor):
    Package = apps.get_model('adminside', 'Package')
    through = Package.categories.through
    rows = [
        through(package_id=package.pk, packagecategory_id=package.category_id)
        for package in Package.objects.exclude(category_id__isnull=True).only('pk', 'category_id')
    ]
    through.objects.bulk_create(rows, ignore_conflicts=True)


class Migration(migrations.Migration):

    dependencies = [
        ('adminside', '0018_package_categories'),
    ]

    operations = [
        migrations.RunPython(copy_primary_category_to_categories, migrations.RunPython.noop),
    ]
