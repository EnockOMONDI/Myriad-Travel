"""
Django management command to debug template issues
"""

from django.core.management.base import BaseCommand
from django.template.loader import get_template
from django.template import TemplateDoesNotExist, TemplateSyntaxError
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Debug template issues for Mbugani Luxe Adventures backup templates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--template',
            type=str,
            help='Specific template to debug (e.g., users/indexbackup.html)',
        )
        parser.add_argument(
            '--check-all',
            action='store_true',
            help='Check all backup templates',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 TEMPLATE DEBUG TOOL - Mbugani Luxe Adventures')
        )
        self.stdout.write('=' * 60)

        if options['template']:
            self.debug_single_template(options['template'])
        elif options['check_all']:
            self.debug_backup_templates()
        else:
            self.show_help()

    def debug_single_template(self, template_name):
        """Debug a specific template"""
        self.stdout.write(f"\n🔍 Debugging template: {template_name}")
        self.stdout.write('-' * 40)

        try:
            template = get_template(template_name)
            self.stdout.write(
                self.style.SUCCESS(f"✅ Template found: {template.origin.name}")
            )
            
            # Check template source
            with open(template.origin.name, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
            self.stdout.write(f"📄 Template has {len(lines)} lines")
            
            # Check for common issues
            self.check_template_issues(content, template_name)
            
        except TemplateDoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Template not found: {template_name}")
            )
        except TemplateSyntaxError as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Template syntax error: {e}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error loading template: {e}")
            )

    def debug_backup_templates(self):
        """Debug all backup templates"""
        backup_templates = [
            'users/indexbackup.html',
            'users/navbarbackup.html',
            'users/basebackup.html',
            'users/indexbackup2.html',
        ]

        self.stdout.write("\n🔍 Checking all backup templates...")
        self.stdout.write('-' * 40)

        for template_name in backup_templates:
            self.debug_single_template(template_name)

    def check_template_issues(self, content, template_name):
        """Check for common template issues"""
        issues = []
        
        # Check for extends
        if 'extends' in content:
            extends_lines = [line.strip() for line in content.split('\n') if 'extends' in line]
            for line in extends_lines:
                self.stdout.write(f"🔗 Extends: {line}")
        
        # Check for includes
        if 'include' in content:
            include_lines = [line.strip() for line in content.split('\n') if 'include' in line]
            for line in include_lines:
                self.stdout.write(f"📎 Include: {line}")
        
        # Check for static files
        if 'static' in content:
            static_count = content.count('{% static')
            self.stdout.write(f"📁 Static file references: {static_count}")
        
        # Check for URL references
        if 'url' in content:
            url_count = content.count('{% url')
            self.stdout.write(f"🔗 URL references: {url_count}")
        
        # Check for block tags
        block_count = content.count('{% block')
        endblock_count = content.count('{% endblock')
        if block_count != endblock_count:
            issues.append(f"Mismatched block tags: {block_count} blocks, {endblock_count} endblocks")
        
        # Check for load tags
        if '{% load static %}' not in content and '{% static' in content:
            issues.append("Static files used but '{% load static %}' not found")
        
        if issues:
            self.stdout.write(self.style.WARNING("\n⚠️  Potential Issues:"))
            for issue in issues:
                self.stdout.write(self.style.WARNING(f"   - {issue}"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ No obvious issues found"))

    def show_help(self):
        """Show usage help"""
        self.stdout.write("\n📖 Usage Examples:")
        self.stdout.write("python manage.py debug_templates --template users/indexbackup.html")
        self.stdout.write("python manage.py debug_templates --check-all")
        self.stdout.write("\n🔧 Template Debugging Tips:")
        self.stdout.write("1. Check template inheritance chain")
        self.stdout.write("2. Verify static file references")
        self.stdout.write("3. Ensure URL patterns exist")
        self.stdout.write("4. Check for missing {% load %} tags")
        self.stdout.write("5. Verify block tag matching")
