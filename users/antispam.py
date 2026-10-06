"""Small, provider-backed protections for public enquiry forms."""

import hashlib
import logging

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django import forms

logger = logging.getLogger(__name__)


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR', '')


def validate_turnstile(token, request):
    secret = getattr(settings, 'TURNSTILE_SECRET', '') or getattr(settings, 'TURNSTILE_SECRET_KEY', '')
    if not secret:
        return True
    if not token:
        return False
    try:
        response = requests.post(
            'https://challenges.cloudflare.com/turnstile/v0/siteverify',
            data={'secret': secret, 'response': token, 'remoteip': client_ip(request)},
            timeout=(3, 8),
        )
        response.raise_for_status()
        result = response.json()
        if not result.get('success'):
            return False
        hostname = (result.get('hostname') or '').lower()
        allowed = getattr(settings, 'TURNSTILE_ALLOWED_HOSTNAMES', set())
        return not allowed or hostname in allowed
    except (requests.RequestException, ValueError):
        logger.exception('Turnstile validation failed')
        return False


def check_form_submission(request, email=''):
    """Apply a modest per-IP and per-email window before email/database writes."""
    window = 15 * 60
    ip_digest = hashlib.sha256(client_ip(request).encode()).hexdigest()[:24]
    email_digest = hashlib.sha256(email.strip().lower().encode()).hexdigest()[:24] if email else ''
    keys = [(f'public-form:ip:{ip_digest}', 5)]
    if email_digest:
        keys.append((f'public-form:email:{email_digest}', 3))

    for key, limit in keys:
        count = cache.get(key, 0)
        if count >= limit:
            return False
    for key, _ in keys:
        cache.set(key, cache.get(key, 0) + 1, window)
    return True


class AntiSpamFormMixin:
    website = None

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)
        self.fields['website'] = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean(self):
        cleaned = super().clean()
        if self.data.get('website'):
            raise ValidationError('Unable to submit this request.')
        token = self.data.get('cf-turnstile-response', '')
        if self.request and not validate_turnstile(token, self.request):
            raise ValidationError('Please complete the security check and try again.')
        return cleaned
