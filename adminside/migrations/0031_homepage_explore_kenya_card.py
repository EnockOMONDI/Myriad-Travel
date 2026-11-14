from django.db import migrations, models
import django.db.models.deletion
import pyuploadcare.dj.models


DEFAULT_CARDS = (
    {
        'slug': 'kenyan-coast',
        'name': 'Kenyan Coast',
        'description': 'Beach stays, marine escapes and relaxed coastal holidays.',
        'icon': 'waves',
        'url': '/kenyan-coast/',
        'action_label': 'Explore Kenyan Coast',
        'display_order': 1,
    },
    {
        'slug': 'safaris',
        'name': 'Safaris',
        'description': 'Wildlife, open landscapes and expertly planned safari circuits.',
        'icon': 'binoculars',
        'url': '/safaris/',
        'action_label': 'Explore Safaris',
        'display_order': 2,
    },
    {
        'slug': 'getaways',
        'name': 'Getaways',
        'description': 'Scenic breaks, short holidays and easy escapes from Nairobi.',
        'icon': 'map',
        'url': '/getaways/',
        'action_label': 'Explore Getaways',
        'display_order': 3,
    },
    {
        'slug': 'day-trips',
        'name': 'Day Trips',
        'description': 'Well-planned one-day adventures, hikes and weekend experiences.',
        'icon': 'sunrise',
        'url': '/day-trips/',
        'action_label': 'Explore Day Trips',
        'display_order': 4,
    },
    {
        'slug': 'seasonal-packages',
        'name': 'Seasonal Packages',
        'description': 'Holiday ideas shaped around Kenya’s most anticipated seasons.',
        'icon': 'calendar-days',
        'url': '/seasonal-packages/',
        'action_label': 'Explore Seasonal Packages',
        'display_order': 5,
    },
    {
        'slug': 'deals',
        'name': 'Deals',
        'description': 'Current offers and limited-date experiences worth discovering.',
        'icon': 'tag',
        'url': '/deals/',
        'action_label': 'View Current Deals',
        'display_order': 6,
    },
)


def seed_cards(apps, schema_editor):
    ContentSection = apps.get_model('adminside', 'ContentSection')
    Card = apps.get_model('adminside', 'HomepageExploreCard')
    section, _ = ContentSection.objects.get_or_create(
        section_key='homepage-explore-kenya',
        defaults={
            'name': 'Homepage Explore Kenya',
            'eyebrow': 'Explore Kenya',
            'title': 'Kenya, beyond the usual route',
            'description': 'Safari circuits, coastal stays, northern-frontier adventures and weekend escapes.',
            'is_active': True,
        },
    )
    for card in DEFAULT_CARDS:
        Card.objects.get_or_create(section=section, slug=card['slug'], defaults=card)


class Migration(migrations.Migration):
    dependencies = [
        ('adminside', '0030_content_section_eyebrow_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='HomepageExploreCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(help_text='Stable card key, for example kenyan-coast.', max_length=80)),
                ('name', models.CharField(max_length=120)),
                ('description', models.CharField(blank=True, max_length=240)),
                ('icon', models.CharField(default='map', max_length=40)),
                ('image', pyuploadcare.dj.models.ImageField(blank=True, help_text='Optional Uploadcare image. Recommended display size: 1200 × 800px. Static fallback remains active when empty.', manual_crop='1200x800', null=True)),
                ('url', models.CharField(help_text='Myriad page path, for example /kenyan-coast/.', max_length=300)),
                ('action_label', models.CharField(default='Explore', max_length=80)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('section', models.ForeignKey(help_text='Normally Homepage Explore Kenya. Keep this unchanged.', on_delete=django.db.models.deletion.CASCADE, related_name='explore_kenya_cards', to='adminside.contentsection')),
            ],
            options={
                'verbose_name': 'Homepage Explore Kenya Card',
                'verbose_name_plural': 'Homepage Explore Kenya Cards',
                'ordering': ['display_order', 'id'],
            },
        ),
        migrations.AddConstraint(
            model_name='homepageexplorecard',
            constraint=models.UniqueConstraint(fields=('section', 'slug'), name='unique_explore_card_per_section'),
        ),
        migrations.RunPython(seed_cards, migrations.RunPython.noop),
    ]
