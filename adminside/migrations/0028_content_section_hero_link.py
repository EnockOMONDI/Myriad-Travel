from django.db import migrations, models
import django.db.models.deletion


def seed_homepage_hero(apps, schema_editor):
    ContentSection = apps.get_model('adminside', 'ContentSection')
    ContentSection.objects.get_or_create(
        section_key='homepage-hero',
        defaults={
            'name': 'Homepage Hero',
            'title': 'Beyond Imagination',
            'description': '',
            'cta_text': 'Take Me There',
            'cta_url': '/explore-kenya/',
            'is_active': True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ('adminside', '0027_destination_things_to_do'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section_key', models.SlugField(help_text='Stable internal key. Do not change it after the section is created.', max_length=80, unique=True)),
                ('name', models.CharField(help_text='Friendly name shown to the content team, for example Homepage Hero.', max_length=120)),
                ('title', models.CharField(blank=True, help_text='Main heading shown in this section.', max_length=200)),
                ('description', models.TextField(blank=True, help_text='Short supporting copy. Keep it concise for the public page.')),
                ('cta_text', models.CharField(blank=True, help_text='Optional button label, for example Explore Kenya.', max_length=80)),
                ('cta_url', models.CharField(blank=True, help_text='Optional site path or full URL, for example /explore-kenya/.', max_length=300)),
                ('is_active', models.BooleanField(default=True, help_text='Turn the section off only when the page should hide it.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Content Section',
                'verbose_name_plural': 'Content Sections',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='heroslider',
            name='section',
            field=models.ForeignKey(blank=True, help_text='The content section this slide belongs to. Leave blank only for legacy fallback slides.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='hero_slides', to='adminside.contentsection'),
        ),
        migrations.RunPython(seed_homepage_hero, migrations.RunPython.noop),
    ]
