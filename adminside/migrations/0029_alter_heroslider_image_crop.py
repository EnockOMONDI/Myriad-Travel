from django.db import migrations
import pyuploadcare.dj.models


class Migration(migrations.Migration):
    dependencies = [
        ('adminside', '0028_content_section_hero_link'),
    ]

    operations = [
        migrations.AlterField(
            model_name='heroslider',
            name='image',
            field=pyuploadcare.dj.models.ImageField(
                help_text='Hero slider image (recommended size: 2048x768px, wide 8:3 composition)',
                manual_crop='2048x768',
            ),
        ),
    ]
