from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0011_quoterequest_citizenship'),
    ]

    operations = [
        migrations.AddField(
            model_name='quoterequest',
            name='quoted_value',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Final quote amount prepared for the client. Leave blank until pricing is confirmed.',
                max_digits=10,
                null=True,
            ),
        ),
    ]
