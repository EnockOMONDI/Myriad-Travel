from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('adminside', '0022_add_multicountry_destination_grouping')]

    operations = [
        migrations.CreateModel(
            name='DayTripDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('duration_label', models.CharField(choices=[('Half day', 'Half day'), ('Full day', 'Full day')], max_length=30)),
                ('departs_from', models.CharField(max_length=160)),
                ('price_audience', models.CharField(default='Kenyan citizen adult', max_length=160)),
                ('price_basis', models.CharField(max_length=200)),
                ('price_status', models.CharField(choices=[('proposed', 'Proposed'), ('confirmed', 'Confirmed')], default='proposed', max_length=12)),
                ('schedule', models.TextField(help_text='One timed stop per line, including the time and activity.')),
                ('booking_note', models.TextField(default='Timings are approximate. Myriad Travel confirms the final price and departure when you enquire.')),
                ('package', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='day_trip_details', to='adminside.package')),
            ],
            options={'verbose_name_plural': 'Day trip details'},
        ),
    ]
