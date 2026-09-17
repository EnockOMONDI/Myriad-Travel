from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
import json

class Command(BaseCommand):
    help = 'Sync production database with local development data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dump-only',
            action='store_true',
            help='Only dump data from local database, do not load into production',
        )
        parser.add_argument(
            '--load-only',
            action='store_true',
            help='Only load data into production database, do not dump from local',
        )

    def handle(self, *args, **options):
        dump_file = 'production_sync_data.json'

        if not options['load_only']:
            self.stdout.write('📤 Dumping data from local database...')

            # Dump data from local database
            with open(dump_file, 'w') as f:
                call_command(
                    'dumpdata',
                    'adminside',
                    'auth.User',
                    '--indent=2',
                    stdout=f,
                    verbosity=1
                )

            self.stdout.write(
                self.style.SUCCESS(f'✅ Data dumped to {dump_file}')
            )

        if not options['dump_only']:
            if os.path.exists(dump_file):
                self.stdout.write('📥 Loading data into production database...')

                try:
                    # Load data into production database
                    call_command(
                        'loaddata',
                        dump_file,
                        verbosity=1
                    )

                    self.stdout.write(
                        self.style.SUCCESS('✅ Data loaded into production database')
                    )

                    # Run create_sample_itineraries command
                    self.stdout.write('🎯 Creating sample itineraries...')
                    call_command('create_sample_itineraries', verbosity=1)

                    self.stdout.write(
                        self.style.SUCCESS('✅ Sample itineraries created')
                    )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error loading data: {e}')
                    )
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Dump file {dump_file} not found')
                )

        self.stdout.write(
            self.style.SUCCESS('🎉 Production sync completed!')
        )