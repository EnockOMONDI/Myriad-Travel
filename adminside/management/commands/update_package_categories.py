"""
Django management command to update package categories for Mbugani Luxe Adventures.
This command will:
1. Create 3 new package categories (Nairobi Excursions, Kenyan Multi-Day Safaris, Outbound Packages)
2. Intelligently reassign existing packages to appropriate categories based on destination and duration
3. Provide detailed logging of all changes

Usage:
    python manage.py update_package_categories
    python manage.py update_package_categories --dry-run  # Preview changes without committing
    DJANGO_ENV=production python manage.py update_package_categories  # Run on production
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from adminside.models import PackageCategory, Package, Destination
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Update package categories for Mbugani Luxe Adventures'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without committing to database',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING('=' * 80))
        self.stdout.write(self.style.WARNING('MBUGANI LUXE ADVENTURES - PACKAGE CATEGORY UPDATE'))
        self.stdout.write(self.style.WARNING('=' * 80))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN MODE: No changes will be saved to database\n'))
        else:
            self.stdout.write(self.style.WARNING('\n⚠️  LIVE MODE: Changes will be saved to database'))
            confirm = input('\nAre you sure you want to continue? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.ERROR('\n❌ Operation cancelled by user.\n'))
                return
            self.stdout.write('')
        
        # Track changes for summary
        changes_log = {
            'categories_created': [],
            'packages_reassigned': [],
            'packages_unchanged': [],
            'packages_set_to_null': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with transaction.atomic():
                # Step 1: Create new categories
                self.stdout.write('[STEP 1] Creating package categories...')
                categories_data = [
                    {
                        'name': 'Nairobi Excursions',
                        'slug': 'nairobi-excursions',
                        'description': 'One-day packages and tours within Nairobi and surrounding areas',
                        'display_order': 1
                    },
                    {
                        'name': 'Kenyan Multi-Day Bush Safaris',
                        'slug': 'kenyan-multiday-safaris',
                        'description': 'Multi-day safari packages within Kenya (excluding Nairobi day trips)',
                        'display_order': 2
                    },
                    {
                        'name': 'Outbound Packages',
                        'slug': 'outbound-packages',
                        'description': 'International packages and tours outside Kenya',
                        'display_order': 3
                    },
                ]
                
                created_categories = {}
                for cat_data in categories_data:
                    category, created = PackageCategory.objects.update_or_create(
                        slug=cat_data['slug'],
                        defaults={
                            'name': cat_data['name'],
                            'description': cat_data['description'],
                            'display_order': cat_data['display_order'],
                            'is_active': True
                        }
                    )
                    created_categories[cat_data['slug']] = category
                    status = 'Created' if created else 'Updated'
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {status}: {category.name}'))
                    changes_log['categories_created'].append({
                        'name': category.name,
                        'slug': category.slug,
                        'status': status
                    })
                
                # Step 2: Get all packages
                self.stdout.write('\n[STEP 2] Analyzing existing packages...')
                packages = Package.objects.select_related('main_destination', 'category').all()
                total_packages = packages.count()
                self.stdout.write(f'  Found {total_packages} packages to process')
                
                # Step 3: Categorize packages
                self.stdout.write('\n[STEP 3] Reassigning packages to categories...')
                
                # Get Kenya country destination
                kenya_destinations = Destination.objects.filter(
                    name__icontains='Kenya',
                    destination_type=Destination.COUNTRY
                )
                kenya = kenya_destinations.first() if kenya_destinations.exists() else None
                
                # Get Nairobi destination
                nairobi_destinations = Destination.objects.filter(
                    name__icontains='Nairobi'
                )
                nairobi = nairobi_destinations.first() if nairobi_destinations.exists() else None
                
                for package in packages:
                    old_category = package.category.name if package.category else 'None'
                    new_category = self._determine_category(
                        package, 
                        created_categories,
                        kenya,
                        nairobi
                    )
                    
                    if new_category:
                        package.category = new_category
                        package.save()
                        
                        log_entry = {
                            'package_name': package.name,
                            'package_slug': package.slug,
                            'old_category': old_category,
                            'new_category': new_category.name,
                            'destination': package.main_destination.name,
                            'duration_days': package.duration_days,
                            'reason': self._get_categorization_reason(package, new_category, kenya, nairobi)
                        }
                        
                        if old_category == new_category.name:
                            changes_log['packages_unchanged'].append(log_entry)
                            self.stdout.write(f'  ○ {package.name} → {new_category.name} (unchanged)')
                        else:
                            changes_log['packages_reassigned'].append(log_entry)
                            self.stdout.write(self.style.SUCCESS(
                                f'  ✓ {package.name} → {new_category.name} '
                                f'(was: {old_category})'
                            ))
                    else:
                        # Set to null for manual review
                        package.category = None
                        package.save()
                        
                        changes_log['packages_set_to_null'].append({
                            'package_name': package.name,
                            'package_slug': package.slug,
                            'old_category': old_category,
                            'destination': package.main_destination.name,
                            'duration_days': package.duration_days,
                            'reason': 'Could not determine appropriate category - needs manual review'
                        })
                        
                        self.stdout.write(self.style.WARNING(
                            f'  ⚠ {package.name} → NULL (needs manual review)'
                        ))
                
                # Step 4: Summary
                self.stdout.write('\n' + '=' * 80)
                self.stdout.write(self.style.SUCCESS('SUMMARY'))
                self.stdout.write('=' * 80)
                self.stdout.write(f'Total packages processed: {total_packages}')
                self.stdout.write(f'  ✓ Reassigned: {len(changes_log["packages_reassigned"])}')
                self.stdout.write(f'  ○ Unchanged: {len(changes_log["packages_unchanged"])}')
                self.stdout.write(f'  ⚠ Set to NULL (manual review needed): {len(changes_log["packages_set_to_null"])}')
                self.stdout.write(f'\nCategories created/updated: {len(changes_log["categories_created"])}')
                
                for cat in created_categories.values():
                    count = Package.objects.filter(category=cat).count()
                    self.stdout.write(f'  • {cat.name}: {count} packages')
                
                # Save changes log to file
                log_filename = f'package_category_changes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                with open(log_filename, 'w') as f:
                    json.dump(changes_log, f, indent=2)
                self.stdout.write(f'\n📄 Detailed changes log saved to: {log_filename}')
                
                if dry_run:
                    self.stdout.write(self.style.WARNING('\n🔍 DRY RUN: Rolling back all changes...'))
                    raise Exception("Dry run - rolling back transaction")
                else:
                    self.stdout.write(self.style.SUCCESS('\n✅ All changes committed to database!'))
                
                self.stdout.write('=' * 80 + '\n')
                
        except Exception as e:
            if dry_run:
                self.stdout.write(self.style.SUCCESS('\n✅ Dry run completed successfully!\n'))
            else:
                self.stdout.write(self.style.ERROR(f'\n❌ Error: {str(e)}\n'))
                raise

    def _determine_category(self, package, categories, kenya, nairobi):
        """
        Determine the appropriate category for a package based on destination and duration.
        """
        destination = package.main_destination
        duration_days = package.duration_days
        
        # Check if destination is in Kenya
        is_kenya = self._is_kenya_destination(destination, kenya)
        is_nairobi = self._is_nairobi_destination(destination, nairobi)
        
        # Categorization logic
        if is_nairobi and duration_days == 1:
            # Nairobi day trips
            return categories['nairobi-excursions']
        elif is_kenya and duration_days > 1:
            # Multi-day Kenya safaris
            return categories['kenyan-multiday-safaris']
        elif not is_kenya:
            # International/outbound packages
            return categories['outbound-packages']
        elif is_kenya and duration_days == 1 and not is_nairobi:
            # Other Kenya day trips (could be Nairobi excursions or safaris)
            # Default to Nairobi Excursions for day trips
            return categories['nairobi-excursions']
        else:
            # Unclear - return None for manual review
            return None

    def _is_kenya_destination(self, destination, kenya):
        """Check if destination is in Kenya"""
        if not destination:
            return False
        
        # Check if destination name contains Kenya
        if 'kenya' in destination.name.lower():
            return True
        
        # Check parent hierarchy
        current = destination
        while current:
            if 'kenya' in current.name.lower():
                return True
            current = current.parent
        
        return False

    def _is_nairobi_destination(self, destination, nairobi):
        """Check if destination is Nairobi or within Nairobi"""
        if not destination:
            return False
        
        # Check if destination name contains Nairobi
        if 'nairobi' in destination.name.lower():
            return True
        
        # Check parent hierarchy
        current = destination
        while current:
            if 'nairobi' in current.name.lower():
                return True
            current = current.parent
        
        return False

    def _get_categorization_reason(self, package, category, kenya, nairobi):
        """Get human-readable reason for categorization"""
        is_kenya = self._is_kenya_destination(package.main_destination, kenya)
        is_nairobi = self._is_nairobi_destination(package.main_destination, nairobi)
        duration = package.duration_days
        
        if category.slug == 'nairobi-excursions':
            if is_nairobi and duration == 1:
                return f'Nairobi-based day trip ({duration} day)'
            else:
                return f'Kenya day trip ({duration} day)'
        elif category.slug == 'kenyan-multiday-safaris':
            return f'Multi-day Kenya safari ({duration} days)'
        elif category.slug == 'outbound-packages':
            return f'International destination ({package.main_destination.name})'
        else:
            return 'Unknown'

