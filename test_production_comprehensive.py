#!/usr/bin/env python
"""
Comprehensive Production Testing Script for Mbugani Luxe Adventures
Tests all critical functionality in production environment
"""

import os
import sys
import django

# Set production environment
os.environ['DJANGO_ENV'] = 'production'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tours_travels.settings_prod')

django.setup()

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from users.tasks import send_email_via_mailtrap
from users.models import QuoteRequest, Destination, Package
from pyuploadcare import Uploadcare
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Test results storage
test_results = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def log_test(test_name, passed, message=""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    full_message = f"{status}: {test_name}"
    if message:
        full_message += f" - {message}"
    
    logger.info(full_message)
    
    if passed:
        test_results['passed'].append(test_name)
    else:
        test_results['failed'].append((test_name, message))

def log_warning(test_name, message):
    """Log warning"""
    logger.warning(f"⚠️  WARNING: {test_name} - {message}")
    test_results['warnings'].append((test_name, message))

print("=" * 80)
print("🧪 MBUGANI LUXE ADVENTURES - COMPREHENSIVE PRODUCTION TESTING")
print("=" * 80)
print()

# ============================================================================
# TEST 1: ENVIRONMENT VARIABLES VALIDATION
# ============================================================================
print("📋 TEST 1: Environment Variables Validation")
print("-" * 80)

required_vars = {
    'SECRET_KEY': 'Django secret key',
    'DATABASE_URL': 'PostgreSQL connection string',
    'MAILTRAP_API_TOKEN': 'Mailtrap API token',
    'UPLOADCARE_PUBLIC_KEY': 'Uploadcare public key',
    'UPLOADCARE_SECRET_KEY': 'Uploadcare secret key',
    'DEFAULT_FROM_EMAIL': 'Default from email',
    'ADMIN_EMAIL': 'Admin email',
    'SITE_URL': 'Site URL',
    'WHATSAPP_PHONE': 'WhatsApp phone number',
}

for var_name, description in required_vars.items():
    value = os.getenv(var_name)
    if value:
        # Mask sensitive values
        if 'KEY' in var_name or 'TOKEN' in var_name or 'URL' in var_name:
            display_value = value[:10] + "..." if len(value) > 10 else "***"
        else:
            display_value = value
        log_test(f"Env var: {var_name}", True, f"{description} = {display_value}")
    else:
        log_test(f"Env var: {var_name}", False, f"{description} is missing")

# Check Django environment
django_env = os.getenv('DJANGO_ENV')
if django_env == 'production':
    log_test("DJANGO_ENV", True, "Set to 'production'")
else:
    log_test("DJANGO_ENV", False, f"Expected 'production', got '{django_env}'")

# Check DEBUG mode
if settings.DEBUG == False:
    log_test("DEBUG mode", True, "Correctly set to False")
else:
    log_test("DEBUG mode", False, "Should be False in production")

print()

# ============================================================================
# TEST 2: DATABASE CONNECTION
# ============================================================================
print("📋 TEST 2: Database Connection Testing")
print("-" * 80)

try:
    # Test database connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]
        log_test("Database connection", True, f"Connected to PostgreSQL")
        logger.info(f"   Database version: {db_version[:50]}...")
    
    # Test database queries
    destination_count = Destination.objects.count()
    package_count = Package.objects.count()
    quote_count = QuoteRequest.objects.count()
    
    log_test("Database queries", True, f"Destinations: {destination_count}, Packages: {package_count}, Quotes: {quote_count}")
    
except Exception as e:
    log_test("Database connection", False, str(e))

print()

# ============================================================================
# TEST 3: SECURITY SETTINGS
# ============================================================================
print("📋 TEST 3: Production Security Settings")
print("-" * 80)

security_checks = {
    'SECURE_SSL_REDIRECT': (settings.SECURE_SSL_REDIRECT, True),
    'SECURE_HSTS_SECONDS': (settings.SECURE_HSTS_SECONDS, 31536000),
    'SECURE_HSTS_INCLUDE_SUBDOMAINS': (settings.SECURE_HSTS_INCLUDE_SUBDOMAINS, True),
    'SECURE_HSTS_PRELOAD': (settings.SECURE_HSTS_PRELOAD, True),
    'SECURE_CONTENT_TYPE_NOSNIFF': (settings.SECURE_CONTENT_TYPE_NOSNIFF, True),
    'X_FRAME_OPTIONS': (settings.X_FRAME_OPTIONS, 'DENY'),
}

for setting_name, (actual, expected) in security_checks.items():
    if actual == expected:
        log_test(f"Security: {setting_name}", True, f"= {actual}")
    else:
        log_test(f"Security: {setting_name}", False, f"Expected {expected}, got {actual}")

print()

# ============================================================================
# TEST 4: MAILTRAP EMAIL API
# ============================================================================
print("📋 TEST 4: Mailtrap Email API Testing")
print("-" * 80)

# Check Mailtrap token
if settings.MAILTRAP_API_TOKEN:
    log_test("Mailtrap API token", True, "Token is configured")
    
    # Test email sending
    try:
        test_subject = "🧪 Mbugani Luxe Adventures - Production Test Email"
        test_html = """
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #291c1a;">Production Environment Test</h2>
            <p>This is a test email from the Mbugani Luxe Adventures production environment.</p>
            <p><strong>Test Details:</strong></p>
            <ul>
                <li>Environment: Production</li>
                <li>Email Service: Mailtrap HTTP API</li>
                <li>Django Settings: tours_travels.settings_prod</li>
                <li>Database: Supabase PostgreSQL</li>
            </ul>
            <p style="color: #bd8c06;">If you received this email, the email system is working correctly! ✅</p>
            <hr>
            <p style="font-size: 12px; color: #666;">
                Mbugani Luxe Adventures<br>
                Luxury Safari & Adventure Tourism<br>
                Phone: +254701810167
            </p>
        </body>
        </html>
        """
        
        test_recipient = "djseanizellkenya@gmail.com"
        
        logger.info(f"   Sending test email to {test_recipient}...")
        success = send_email_via_mailtrap(
            subject=test_subject,
            html_message=test_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_recipient]
        )
        
        if success:
            log_test("Email sending", True, f"Test email sent to {test_recipient}")
        else:
            log_test("Email sending", False, "Failed to send test email")
            
    except Exception as e:
        log_test("Email sending", False, str(e))
else:
    log_test("Mailtrap API token", False, "Token not configured")

print()

# ============================================================================
# TEST 5: UPLOADCARE CDN
# ============================================================================
print("📋 TEST 5: Uploadcare CDN Integration")
print("-" * 80)

try:
    if settings.UPLOADCARE_PUBLIC_KEY and settings.UPLOADCARE_SECRET_KEY:
        log_test("Uploadcare credentials", True, "Public and secret keys configured")
        
        # Initialize Uploadcare client
        uploadcare = Uploadcare(
            public_key=settings.UPLOADCARE_PUBLIC_KEY,
            secret_key=settings.UPLOADCARE_SECRET_KEY
        )
        
        log_test("Uploadcare client", True, "Client initialized successfully")
        logger.info(f"   Public key: {settings.UPLOADCARE_PUBLIC_KEY}")
        
    else:
        log_test("Uploadcare credentials", False, "Keys not configured")
        
except Exception as e:
    log_test("Uploadcare client", False, str(e))

print()

# ============================================================================
# TEST 6: ALLOWED HOSTS
# ============================================================================
print("📋 TEST 6: Allowed Hosts Configuration")
print("-" * 80)

expected_hosts = [
    'mbuganiapp.onrender.com',
    'www.mbuganiluxeadventures.com',
    'mbuganiluxeadventures.com',
]

for host in expected_hosts:
    if host in settings.ALLOWED_HOSTS:
        log_test(f"Allowed host: {host}", True, "Configured")
    else:
        log_warning(f"Allowed host: {host}", "Not in ALLOWED_HOSTS")

print()

# ============================================================================
# TEST 7: SITE CONFIGURATION
# ============================================================================
print("📋 TEST 7: Site Configuration")
print("-" * 80)

config_checks = {
    'SITE_URL': settings.SITE_URL,
    'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
    'ADMIN_EMAIL': settings.ADMIN_EMAIL,
    'WHATSAPP_PHONE': settings.WHATSAPP_PHONE,
    'TIME_ZONE': settings.TIME_ZONE,
}

for config_name, value in config_checks.items():
    if value:
        log_test(f"Config: {config_name}", True, f"= {value}")
    else:
        log_test(f"Config: {config_name}", False, "Not configured")

print()

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("=" * 80)
print("📊 TEST SUMMARY")
print("=" * 80)

total_tests = len(test_results['passed']) + len(test_results['failed'])
pass_rate = (len(test_results['passed']) / total_tests * 100) if total_tests > 0 else 0

print(f"\n✅ PASSED: {len(test_results['passed'])} tests")
print(f"❌ FAILED: {len(test_results['failed'])} tests")
print(f"⚠️  WARNINGS: {len(test_results['warnings'])} warnings")
print(f"📈 PASS RATE: {pass_rate:.1f}%")

if test_results['failed']:
    print("\n❌ FAILED TESTS:")
    for test_name, message in test_results['failed']:
        print(f"   - {test_name}: {message}")

if test_results['warnings']:
    print("\n⚠️  WARNINGS:")
    for test_name, message in test_results['warnings']:
        print(f"   - {test_name}: {message}")

print("\n" + "=" * 80)

if len(test_results['failed']) == 0:
    print("🎉 ALL TESTS PASSED! Production environment is ready.")
    sys.exit(0)
else:
    print("⚠️  SOME TESTS FAILED. Please review and fix issues above.")
    sys.exit(1)

