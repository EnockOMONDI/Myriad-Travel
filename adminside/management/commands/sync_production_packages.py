from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
import json

class Command(BaseCommand):
    help = 'Sync only packages and related data from local to production database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dump-only',
            action='store_true',
            help='Only dump packages data from local database, do not load into production',
        )
        parser.add_argument(
            '--load-only',
            action='store_true',
            help='Only load packages data into production database, do not dump from local',
        )

    def handle(self, *args, **options):
        dump_file = 'production_packages_data.json'

        if not options['load_only']:
            self.stdout.write('📤 Dumping packages data from local database...')

            # Dump only packages and related data (exclude users and potentially conflicting data)
            with open(dump_file, 'w') as f:
                call_command(
                    'dumpdata',
                    'adminside',  # Only dump adminside app data
                    '--indent=2',
                    stdout=f,
                    verbosity=1
                )

            self.stdout.write(
                self.style.SUCCESS(f'✅ Packages data dumped to {dump_file}')
            )

            # Show summary of dumped data
            with open(dump_file, 'r') as f:
                content = f.read()
                package_count = content.count('"model": "adminside.package"')
                destination_count = content.count('"model": "adminside.destination"')
                itinerary_count = content.count('"model": "adminside.itinerary"')
                day_count = content.count('"model": "adminside.itineraryday"')

            self.stdout.write(f'📊 Dump Summary:')
            self.stdout.write(f'   📦 Packages: {package_count}')
            self.stdout.write(f'   🗺️  Destinations: {destination_count}')
            self.stdout.write(f'   🗺️  Itineraries: {itinerary_count}')
            self.stdout.write(f'   📅 Days: {day_count}')

        if not options['dump_only']:
            if os.path.exists(dump_file):
                self.stdout.write('📥 Loading packages data into production database...')

                try:
                    # Clear existing packages data first (optional - be careful!)
                    from adminside.models import Package, Destination, Itinerary, ItineraryDay, TravelMode, Accommodation

                    # Count existing data
                    existing_packages = Package.objects.count()
                    existing_destinations = Destination.objects.count()
                    existing_itineraries = Itinerary.objects.count()

                    self.stdout.write(f'📊 Existing data: {existing_packages} packages, {existing_destinations} destinations, {existing_itineraries} itineraries')

                    # Ask for confirmation before clearing (uncomment if needed)
                    # if existing_packages > 0:
                    #     self.stdout.write(self.style.WARNING('⚠️  Existing packages found. This will replace them.'))
                    #     if input('Continue? (y/N): ').lower() != 'y':
                    #         self.stdout.write('❌ Operation cancelled')
                    #         return

                    # Clear existing data (be careful with this!)
                    # Package.objects.all().delete()
                    # Destination.objects.all().delete()
                    # Itinerary.objects.all().delete()
                    # ItineraryDay.objects.all().delete()

                    # Load the packages data
                    call_command(
                        'loaddata',
                        dump_file,
                        verbosity=1
                    )

                    self.stdout.write(
                        self.style.SUCCESS('✅ Packages data loaded into production database')
                    )

                    # Run create_sample_itineraries to ensure itineraries are created
                    self.stdout.write('🎯 Ensuring sample itineraries exist...')
                    call_command('create_sample_itineraries', verbosity=1)

                    # Show final counts
                    final_packages = Package.objects.count()
                    final_destinations = Destination.objects.count()
                    final_itineraries = Itinerary.objects.count()
                    packages_with_itineraries = Package.objects.filter(itinerary__isnull=False).distinct().count()

                    self.stdout.write(
                        self.style.SUCCESS('📊 Final Data Counts:')
                    )
                    self.stdout.write(f'   📦 Total Packages: {final_packages}')
                    self.stdout.write(f'   🗺️  Destinations: {final_destinations}')
                    self.stdout.write(f'   🗺️  Itineraries: {final_itineraries}')
                    self.stdout.write(f'   📍 Packages with itineraries: {packages_with_itineraries}')

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error loading packages data: {e}')
                    )
                    self.stdout.write(
                        self.style.WARNING('💡 Try clearing existing data first or check for conflicts')
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Dump file {dump_file} not found')
                )
                self.stdout.write(
                    self.style.WARNING('💡 Run without --load-only flag first to create the dump file')
                )

        self.stdout.write(
            self.style.SUCCESS('🎉 Packages sync completed!')
        )