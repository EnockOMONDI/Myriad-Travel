"""
Test settings for Mbugani Luxe Adventures
Uses SQLite for faster testing and avoids PostgreSQL connection issues
"""

from .settings import *

# Use SQLite for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable migrations for faster testing
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# Speed up password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable debug toolbar for tests
if 'debug_toolbar' in INSTALLED_APPS:
    INSTALLED_APPS.remove('debug_toolbar')

# Remove middleware that might cause issues in tests
MIDDLEWARE = [m for m in MIDDLEWARE if 'debug_toolbar' not in m]

# Test-specific settings
SECRET_KEY = 'test-secret-key-for-testing-only'
DEBUG = False
SITE_URL = 'http://testserver'

# Disable caching for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Media files for testing
MEDIA_ROOT = '/tmp/mbugani_test_media'
MEDIA_URL = '/test_media/'

# Static files for testing
STATIC_ROOT = '/tmp/mbugani_test_static'

# Uploadcare settings for testing
UPLOADCARE = {
    'pub_key': 'test_pub_key',
    'secret': 'test_secret_key',
}
