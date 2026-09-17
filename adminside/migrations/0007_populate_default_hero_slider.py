# Generated manually for Mbugani Luxe Adventures

from django.db import migrations

def create_default_hero_slider(apps, schema_editor):
    """Create default hero slider entry with existing hero image"""
    HeroSlider = apps.get_model('adminside', 'HeroSlider')
    
    # Create default hero slider entry
    HeroSlider.objects.create(
        title="Welcome to Mbugani Luxe Adventures",
        subtitle="Discover Extraordinary Safari & Adventure Experiences in East Africa",
        is_active=True,
        order=1,
        cta_text="Explore Packages",
        cta_url="/packages/"
    )

def reverse_default_hero_slider(apps, schema_editor):
    """Remove default hero slider entry"""
    HeroSlider = apps.get_model('adminside', 'HeroSlider')
    HeroSlider.objects.filter(
        title="Welcome to Mbugani Luxe Adventures"
    ).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('adminside', '0006_add_hero_slider'),
    ]

    operations = [
        migrations.RunPython(
            create_default_hero_slider,
            reverse_default_hero_slider
        ),
    ]
