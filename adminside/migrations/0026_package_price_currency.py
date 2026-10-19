from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminside', '0025_attach_chalbi_packing_items'),
    ]

    operations = [
        migrations.AddField(
            model_name='package',
            name='price_currency',
            field=models.CharField(choices=[('KES', 'Kenyan Shillings (KES)'), ('USD', 'US Dollars (USD)')], default='KES', help_text='Currency for the stored adult sharing rate. Use the currency shown on the approved offer.', max_length=3),
        ),
    ]
