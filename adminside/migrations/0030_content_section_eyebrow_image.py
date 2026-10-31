from django.db import migrations, models
from pyuploadcare.dj.models import ImageField


def seed_home_deals(apps, schema_editor):
    ContentSection = apps.get_model('adminside', 'ContentSection')
    ContentSection.objects.get_or_create(
        section_key='homepage-deals',
        defaults={
            'name': 'Home Deals Section',
            'eyebrow': 'Myriad Travel seasonal offer',
            'title': 'Festive Christmas & New Year Holidays 2026/27',
            'description': 'Celebrate the season with unforgettable escapes across Kenya & beyond.',
            'cta_text': 'Explore Festive Deals',
            'cta_url': '/deals/',
            'is_active': True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ('adminside', '0029_alter_heroslider_image_crop'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentsection',
            name='eyebrow',
            field=models.CharField(blank=True, help_text='Small label above the heading, for example Myriad Travel seasonal offer.', max_length=120),
        ),
        migrations.AddField(
            model_name='contentsection',
            name='image',
            field=ImageField(blank=True, help_text='Optional section image. For Home Deals, use a wide 2172x724px image and keep important subjects away from the edges.', null=True),
        ),
        migrations.RunPython(seed_home_deals, migrations.RunPython.noop),
    ]
