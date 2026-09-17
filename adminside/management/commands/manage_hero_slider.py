from django.core.management.base import BaseCommand
from django.core.files import File
from adminside.models import HeroSlider
import os


class Command(BaseCommand):
    help = 'Manage hero slider entries for Mbugani Luxe Adventures'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all hero slider entries',
        )
        parser.add_argument(
            '--create',
            action='store_true',
            help='Create a new hero slider entry',
        )
        parser.add_argument(
            '--activate',
            type=int,
            help='Activate a hero slider by ID',
        )
        parser.add_argument(
            '--deactivate',
            type=int,
            help='Deactivate a hero slider by ID',
        )
        parser.add_argument(
            '--delete',
            type=int,
            help='Delete a hero slider by ID',
        )
        parser.add_argument(
            '--title',
            type=str,
            help='Title for new hero slider',
        )
        parser.add_argument(
            '--subtitle',
            type=str,
            help='Subtitle for new hero slider',
        )
        parser.add_argument(
            '--order',
            type=int,
            default=0,
            help='Order for new hero slider',
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_sliders()
        elif options['create']:
            self.create_slider(options)
        elif options['activate']:
            self.activate_slider(options['activate'])
        elif options['deactivate']:
            self.deactivate_slider(options['deactivate'])
        elif options['delete']:
            self.delete_slider(options['delete'])
        else:
            self.stdout.write(
                self.style.WARNING('Please specify an action: --list, --create, --activate, --deactivate, or --delete')
            )

    def list_sliders(self):
        """List all hero slider entries"""
        sliders = HeroSlider.objects.all().order_by('order', '-created_at')
        
        if not sliders:
            self.stdout.write(self.style.WARNING('No hero sliders found.'))
            return

        self.stdout.write(self.style.SUCCESS('🎯 HERO SLIDERS'))
        self.stdout.write('=' * 60)
        
        for slider in sliders:
            status = "✅ Active" if slider.is_active else "❌ Inactive"
            image_status = "🖼️  Has Image" if slider.image else "📷 No Image"
            
            self.stdout.write(f"""
ID: {slider.id}
Title: {slider.title or 'No title'}
Subtitle: {slider.subtitle or 'No subtitle'}
Status: {status}
Order: {slider.order}
Image: {image_status}
CTA: {slider.cta_text or 'No CTA'} -> {slider.cta_url or 'No URL'}
Created: {slider.created_at.strftime('%Y-%m-%d %H:%M')}
{'-' * 40}""")

    def create_slider(self, options):
        """Create a new hero slider entry"""
        title = options.get('title') or 'New Hero Slide'
        subtitle = options.get('subtitle') or 'Experience luxury safari adventures'
        order = options.get('order', 0)
        
        slider = HeroSlider.objects.create(
            title=title,
            subtitle=subtitle,
            order=order,
            is_active=True,
            cta_text='Explore Safaris',
            cta_url='/packages/'
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Created hero slider: {slider.title} (ID: {slider.id})')
        )

    def activate_slider(self, slider_id):
        """Activate a hero slider"""
        try:
            slider = HeroSlider.objects.get(id=slider_id)
            slider.is_active = True
            slider.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Activated hero slider: {slider.title}')
            )
        except HeroSlider.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Hero slider with ID {slider_id} not found')
            )

    def deactivate_slider(self, slider_id):
        """Deactivate a hero slider"""
        try:
            slider = HeroSlider.objects.get(id=slider_id)
            slider.is_active = False
            slider.save()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Deactivated hero slider: {slider.title}')
            )
        except HeroSlider.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Hero slider with ID {slider_id} not found')
            )

    def delete_slider(self, slider_id):
        """Delete a hero slider"""
        try:
            slider = HeroSlider.objects.get(id=slider_id)
            title = slider.title
            slider.delete()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Deleted hero slider: {title}')
            )
        except HeroSlider.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Hero slider with ID {slider_id} not found')
            )
