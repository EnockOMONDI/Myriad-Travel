"""Fixed, version-controlled notifications for public service enquiries."""
import logging
from django.conf import settings
from django.template.loader import render_to_string
from .tasks import send_email_via_mailtrap

logger = logging.getLogger(__name__)


SERVICE_EMAIL_CONFIG = {
    'tours': ('Tours & Safaris', 'TOURS_INQUIRY_EMAIL', 'Our safari specialists are reviewing your destination, dates and travel preferences.'),
    'hotels': ('Hotel Booking', 'HOTEL_INQUIRY_EMAIL', 'Our accommodation team is reviewing your dates, room requirements and preferred stay.'),
    'flights': ('Flight Booking', 'FLIGHT_INQUIRY_EMAIL', 'Our flight desk is checking suitable routes, schedules and fare options for your journey.'),
    'transfers': ('Ground Handling & Transfers', 'TRANSFER_INQUIRY_EMAIL', 'Our operations team is reviewing your pickup, destination and transport requirements.'),
    'visa': ('Visa & Travel Advisory', 'VISA_INQUIRY_EMAIL', 'Our advisory team is reviewing the destination and assistance requested. Visa decisions remain with the relevant immigration authority.'),
    'mice': ('Corporate Travel & MICE', 'MICE_INQUIRY_EMAIL', 'Our corporate desk is reviewing your event brief, dates and logistics requirements.'),
    'student': ('Student Travel', 'ADMIN_EMAIL', 'Our team is reviewing your student travel requirements.'),
    'ngo': ('NGO Travel', 'ADMIN_EMAIL', 'Our team is reviewing your organisation’s travel and operational requirements.'),
}


def _recipients(setting_name):
    configured = getattr(settings, setting_name, '') or getattr(settings, 'ADMIN_EMAIL', 'info@myriad-travel.com')
    return [email.strip() for email in configured.split(',') if email.strip()]


def send_service_inquiry_emails(inquiry, form, service_key):
    title, recipient_setting, customer_intro = SERVICE_EMAIL_CONFIG[service_key]
    try:
        fields = []
        for name, field in form.fields.items():
            if name == 'website':
                continue
            display = getattr(inquiry, f'get_{name}_display', None)
            value = display() if display else getattr(inquiry, name, '')
            fields.append((field.label or name.replace('_', ' ').title(), value))
        reference = getattr(inquiry, 'short_reference', str(inquiry.pk))
        context = {
            'title': title,
            'reference': reference,
            'fields': fields,
            'customer_name': inquiry.contact_person,
            'customer_intro': customer_intro,
        }
        admin_sent = send_email_via_mailtrap(
            subject=f'New {title} Inquiry #{reference} from {inquiry.contact_person}',
            html_message=render_to_string('users/emails/service_inquiry_admin.html', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=_recipients(recipient_setting),
        )
        customer_sent = send_email_via_mailtrap(
            subject=f'Your {title} Inquiry #{reference} - Myriad Travel',
            html_message=render_to_string('users/emails/service_inquiry_confirmation.html', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[inquiry.email],
        )
        if hasattr(inquiry, 'admin_notification_sent'):
            inquiry.admin_notification_sent = admin_sent
            inquiry.confirmation_email_sent = customer_sent
            inquiry.save(update_fields=['admin_notification_sent', 'confirmation_email_sent', 'updated_at'])
        return admin_sent and customer_sent
    except Exception:
        logger.exception('Service inquiry notification failed: %s #%s', service_key, inquiry.pk)
        return False
