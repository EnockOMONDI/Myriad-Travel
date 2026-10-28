from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from adminside.models import Campaign, Package


class Command(BaseCommand):
    help = 'Ensure Chalbi and all published packages containing Krisi are active deals.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        ends_on = today + timedelta(days=365)
        packages = Package.objects.filter(status=Package.PUBLISHED).filter(
            name__icontains='Krisi'
        ) | Package.objects.filter(
            status=Package.PUBLISHED,
            slug='twende-chalbi-4-nights-5-days',
        )

        for package in packages.distinct().order_by('name'):
            campaign = Campaign.objects.filter(package=package).order_by('-is_active', '-ends_on', '-pk').first()
            if campaign is None:
                campaign = Campaign(package=package)
            campaign.title = f'{package.name} Deal'
            campaign.starts_on = today
            campaign.ends_on = ends_on
            campaign.is_active = True
            campaign.display_order = 10
            campaign.save()
            self.stdout.write(self.style.SUCCESS(f'active deal: {package.name}'))
