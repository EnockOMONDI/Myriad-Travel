# Generated for Myriad Travel template integration.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminside', '0009_packagecategory_package_category_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='package',
            name='subtitle',
            field=models.CharField(blank=True, help_text='Short package card subtitle for the public website', max_length=280),
        ),
        migrations.AddField(
            model_name='package',
            name='region',
            field=models.CharField(choices=[('kenya-safari', 'Kenya Safaris & Bush'), ('kenya-coast', 'Kenya Coast & Beach'), ('international', 'International Escapes'), ('day-trips', 'Weekend Hikes & Day Trips')], default='kenya-safari', help_text='Frontend collection used by the Myriad package filters', max_length=40),
        ),
        migrations.AddField(
            model_name='package',
            name='lipa_pole_pole',
            field=models.BooleanField(default=False, help_text="Show this package as eligible for Myriad's Lipa Pole Pole plan"),
        ),
        migrations.AddField(
            model_name='package',
            name='lipa_pole_pole_months',
            field=models.PositiveIntegerField(default=4, help_text='Suggested number of monthly installments'),
        ),
        migrations.AddField(
            model_name='package',
            name='highlights',
            field=models.TextField(blank=True, help_text='One public-facing highlight per line for package cards and detail pages'),
        ),
    ]
