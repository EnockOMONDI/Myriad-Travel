"""Notifications for the three public service enquiry forms."""
import logging
from django.conf import settings
from django.template.loader import render_to_string
from .tasks import send_email_via_mailtrap

logger = logging.getLogger(__name__)


def send_service_inquiry_emails(inquiry, form, title):
    try:
        fields = []
        for name, field in form.fields.items():
            display = getattr(inquiry, f'get_{name}_display', None)
            value = display() if display else getattr(inquiry, name)
            fields.append((field.label or name.replace('_', ' ').title(), value))
        context = {'title': title, 'reference': inquiry.pk, 'fields': fields}
        admin_sent = send_email_via_mailtrap(
            subject=f'New {title} Inquiry #{inquiry.pk} from {inquiry.contact_person}',
            html_message=render_to_string('users/emails/service_inquiry_admin.html', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[getattr(settings, 'ADMIN_EMAIL', 'info@mbuganiluxeadventures.com')],
        )
        # The submitted record is retained even when either notification fails.
        customer_sent = send_email_via_mailtrap(
            subject=f'{title} Inquiry Received - Mbugani Luxe Adventures',
            html_message=render_to_string('users/emails/service_inquiry_confirmation.html', context),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[inquiry.email],
        )
        return admin_sent and customer_sent
    except Exception:
        logger.exception('Service inquiry notification failed: %s #%s', title, inquiry.pk)
        return False
