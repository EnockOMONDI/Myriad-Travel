#!/usr/bin/env python
"""
Comprehensive test runner for Mbugani Luxe Adventures booking system
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line


def run_tests():
    """Run all tests for the Mbugani Luxe Adventures booking system"""
    
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tours_travels.settings')
    django.setup()
    
    print("🧪 Starting Comprehensive Test Suite for Mbugani Luxe Adventures")
    print("=" * 60)
    
    # Test categories to run
    test_categories = [
        {
            'name': 'User Model Tests',
            'description': 'Testing user-related database models and relationships',
            'tests': ['users.tests.test_models']
        },
        {
            'name': 'Admin Model Tests',
            'description': 'Testing admin-side database models and relationships',
            'tests': ['adminside.tests.test_models']
        },
        {
            'name': 'Form Persistence Tests',
            'description': 'Testing form data persistence across booking steps',
            'tests': ['users.tests.test_form_persistence']
        },
        {
            'name': 'Booking Flow Integration Tests',
            'description': 'Testing complete booking flow from start to finish',
            'tests': ['users.tests.test_booking_flow']
        },
        {
            'name': 'User Profile & Authentication Tests',
            'description': 'Testing user profile views and authentication',
            'tests': ['users.tests.test_user_views']
        },
        {
            'name': 'Email Functionality Tests',
            'description': 'Testing email sending and template rendering',
            'tests': ['users.tests.test_email_functionality']
        },
        {
            'name': 'Cart Functionality Tests',
            'description': 'Testing shopping cart operations and persistence',
            'tests': ['users.tests.test_cart_functionality']
        },
        {
            'name': 'Responsive Design Tests',
            'description': 'Testing mobile compatibility and responsive design',
            'tests': ['users.tests.test_responsive_design']
        },
        {
            'name': 'Admin Interface Tests',
            'description': 'Testing Django admin interface functionality',
            'tests': ['adminside.tests.test_admin_interface']
        }
    ]
    
    total_tests_run = 0
    failed_categories = []
    
    for category in test_categories:
        print(f"\n📋 {category['name']}")
        print(f"   {category['description']}")
        print("-" * 40)
        
        for test_module in category['tests']:
            print(f"   Running: {test_module}")
            
            # Run the specific test module
            result = os.system(f'python manage.py test {test_module} --verbosity=2')
            
            if result != 0:
                failed_categories.append(category['name'])
                print(f"   ❌ FAILED: {test_module}")
            else:
                print(f"   ✅ PASSED: {test_module}")
            
            total_tests_run += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUITE SUMMARY")
    print("=" * 60)
    
    if failed_categories:
        print(f"❌ {len(failed_categories)} test categories FAILED:")
        for category in failed_categories:
            print(f"   - {category}")
        print(f"\n✅ {len(test_categories) - len(failed_categories)} test categories PASSED")
    else:
        print("🎉 ALL TEST CATEGORIES PASSED!")
    
    print(f"\nTotal test modules run: {total_tests_run}")
    
    # Additional test commands for manual testing
    print("\n" + "=" * 60)
    print("📝 MANUAL TESTING CHECKLIST")
    print("=" * 60)
    
    manual_tests = [
        "1. Guest Booking Flow:",
        "   - Navigate to a package page",
        "   - Complete booking without login",
        "   - Verify account creation and welcome email",
        "",
        "2. Form Persistence:",
        "   - Start booking process",
        "   - Navigate between steps",
        "   - Refresh page and verify data retention",
        "",
        "3. User Dashboard:",
        "   - Login with created account",
        "   - Access user profile dashboard",
        "   - Test bucket list functionality",
        "",
        "4. Email Delivery:",
        "   - Check email inbox for welcome email",
        "   - Check booking confirmation email",
        "   - Verify email formatting and links",
        "",
        "5. Mobile Responsiveness:",
        "   - Test on mobile device or browser dev tools",
        "   - Verify all pages are mobile-friendly",
        "   - Test touch interactions"
    ]
    
    for test in manual_tests:
        print(test)
    
    # Performance and security tests
    print("\n" + "=" * 60)
    print("🔒 SECURITY & PERFORMANCE CHECKLIST")
    print("=" * 60)
    
    security_tests = [
        "□ Password strength validation",
        "□ Session security and timeout",
        "□ CSRF protection on all forms",
        "□ SQL injection prevention",
        "□ XSS protection in templates",
        "□ Email content sanitization",
        "□ User data access control",
        "□ Form validation and error handling"
    ]
    
    for test in security_tests:
        print(test)
    
    print("\n" + "=" * 60)
    print("🚀 DEPLOYMENT READINESS")
    print("=" * 60)
    
    deployment_checklist = [
        "□ All tests passing",
        "□ Database migrations applied",
        "□ Static files collection working",
        "□ Email configuration tested",
        "□ Environment variables configured",
        "□ Debug mode disabled for production",
        "□ Allowed hosts configured",
        "□ SSL/HTTPS configuration",
        "□ Error logging configured",
        "□ Backup strategy in place"
    ]
    
    for item in deployment_checklist:
        print(item)
    
    return len(failed_categories) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
