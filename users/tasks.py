"""
Synchronous email sending using Mailtrap HTTP API for Mbugani Luxe Adventures

This module contains all email sending functions that use Mailtrap's HTTP API
for direct, synchronous email delivery. No background workers required.
"""

import logging
import requests
from mailtrap import Mail, Address, MailtrapClient
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_email_via_mailtrap(subject, html_message, from_email, recipient_list):
    """
    Send email using Mailtrap HTTP API

    Args:
        subject (str): Email subject
        html_message (str): HTML message content
        from_email (str): From email address (e.g., "Mbugani Luxe Adventures <info@mbuganiluxeadventures.com>")
        recipient_list (list): List of recipient email addresses

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        logger.info(f"Sending email via Mailtrap API: subject='{subject}', recipients={recipient_list}")

        # Initialize Mailtrap client
        client = MailtrapClient(token=settings.MAILTRAP_API_TOKEN)

        # Parse from_email to extract name and email
        # Format: "Name <email@example.com>" or just "email@example.com"
        if '<' in from_email and '>' in from_email:
            from_name = from_email.split('<')[0].strip()
            from_email_addr = from_email.split('<')[1].split('>')[0].strip()
        else:
            from_name = "Mbugani Luxe Adventures"
            from_email_addr = from_email.strip()

        # Create mail object
        mail = Mail(
            sender=Address(email=from_email_addr, name=from_name),
            to=[Address(email=email.strip()) for email in recipient_list],
            subject=subject,
            html=html_message,
        )

        # Send email
        # The installed SDK sends without a timeout. Bound HTTPS requests so
        # unavailable email infrastructure cannot exhaust the web worker.
        response = requests.post(client.api_send_url, headers=client.headers,
                                 json=mail.api_data, timeout=(3, 8))
        response.raise_for_status()
        response = response.json()
        if response.get('success') is not True:
            return False

        logger.info(f"Email sent successfully via Mailtrap API: {response}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email via Mailtrap API: {e}")
        return False


def send_quote_request_emails(quote_request_id):
    """
    Send email notifications for quote requests using Mailtrap HTTP API

    Args:
        quote_request_id (int): ID of the QuoteRequest object

    Returns:
        dict: Status of email sending with details
    """
    try:
        # Import here to avoid circular imports
        from users.models import QuoteRequest

        # Get the quote request object
        try:
            quote_request = QuoteRequest.objects.get(id=quote_request_id)
        except QuoteRequest.DoesNotExist:
            error_msg = f"QuoteRequest with ID {quote_request_id} not found"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

        logger.info(f"Sending emails for quote request {quote_request_id}")

        # Track email sending status
        admin_sent = False
        user_sent = False

        # Send admin notification email
        try:
            admin_subject = f'New Quote Request from {quote_request.full_name}'
            admin_message_html = render_to_string('users/emails/quote_request_admin.html', {
                'quote_request': quote_request
            })

            admin_email = getattr(settings, 'ADMIN_EMAIL', 'info@mbuganiluxeadventures.com')

            admin_sent = send_email_via_mailtrap(
                subject=admin_subject,
                html_message=admin_message_html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[admin_email],
            )

            if admin_sent:
                logger.info(f"Admin notification sent for quote request {quote_request_id}")
            else:
                logger.error(f"Failed to send admin email for quote request {quote_request_id}")

        except Exception as e:
            logger.error(f"Failed to send admin email for quote request {quote_request_id}: {e}")

        # Send user confirmation email
        try:
            user_subject = f'Quote Request Received - Mbugani Luxe Adventures'
            user_message_html = render_to_string('users/emails/quote_request_confirmation.html', {
                'quote_request': quote_request
            })

            user_sent = send_email_via_mailtrap(
                subject=user_subject,
                html_message=user_message_html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[quote_request.email],
            )

            if user_sent:
                logger.info(f"User confirmation sent for quote request {quote_request_id}")
            else:
                logger.error(f"Failed to send user email for quote request {quote_request_id}")

        except Exception as e:
            logger.error(f"Failed to send user email for quote request {quote_request_id}: {e}")

        # Update quote request with email status
        try:
            quote_request.admin_notification_sent = admin_sent
            quote_request.confirmation_email_sent = user_sent
            quote_request.save()
            logger.info(f"Updated email status for quote request {quote_request_id}")
        except Exception as e:
            logger.error(f"Failed to update quote request {quote_request_id}: {e}")

        # Return status
        success = admin_sent and user_sent
        result = {
            'success': success,
            'admin_sent': admin_sent,
            'user_sent': user_sent,
            'quote_request_id': quote_request_id,
            'timestamp': timezone.now().isoformat()
        }

        if success:
            logger.info(f"All emails sent successfully for quote request {quote_request_id}")
        else:
            logger.warning(f"Some emails failed for quote request {quote_request_id}: admin={admin_sent}, user={user_sent}")

        return result

    except Exception as e:
        error_msg = f"Unexpected error in quote request email task: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}


def send_job_application_emails(application_id):
    """
    Send email notifications for job applications using Mailtrap HTTP API

    Args:
        application_id (int): ID of the JobApplication object

    Returns:
        dict: Status of email sending with details
    """
    try:
        from users.models import JobApplication

        try:
            job_application = JobApplication.objects.get(id=application_id)
        except JobApplication.DoesNotExist:
            error_msg = f"JobApplication with ID {application_id} not found"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

        logger.info(f"Sending emails for job application {application_id}")

        admin_sent = False
        applicant_sent = False

        # Send admin notification
        try:
            admin_subject = f'New Job Application - {job_application.get_position_display()}'
            admin_message = render_to_string('users/emails/job_application_admin.html', {
                'application': job_application
            })

            careers_email = getattr(settings, 'JOBS_EMAIL', 'careers@mbuganiluxeadventures.com')
            info_email = getattr(settings, 'ADMIN_EMAIL', 'info@mbuganiluxeadventures.com')
            recipient_list = [careers_email, info_email]

            admin_sent = send_email_via_mailtrap(
                subject=admin_subject,
                html_message=admin_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
            )

            if admin_sent:
                logger.info(f"Admin notification sent for job application {application_id}")
            else:
                logger.error(f"Failed to send admin email for job application {application_id}")

        except Exception as e:
            logger.error(f"Failed to send admin email for job application {application_id}: {e}")

        # Send applicant confirmation
        try:
            applicant_subject = f'Application Received - {job_application.get_position_display()}'
            applicant_message = render_to_string('users/emails/job_application_confirmation.html', {
                'application': job_application
            })

            applicant_sent = send_email_via_mailtrap(
                subject=applicant_subject,
                html_message=applicant_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[job_application.email],
            )

            if applicant_sent:
                logger.info(f"Applicant confirmation sent for job application {application_id}")
            else:
                logger.error(f"Failed to send applicant email for job application {application_id}")

        except Exception as e:
            logger.error(f"Failed to send applicant email for job application {application_id}: {e}")

        # Update application status
        try:
            job_application.admin_notification_sent = admin_sent
            job_application.confirmation_email_sent = applicant_sent
            job_application.save()
        except Exception as e:
            logger.error(f"Failed to update job application {application_id}: {e}")

        success = admin_sent and applicant_sent
        result = {
            'success': success,
            'admin_sent': admin_sent,
            'applicant_sent': applicant_sent,
            'application_id': application_id,
            'timestamp': timezone.now().isoformat()
        }

        logger.info(f"Job application emails completed for {application_id}: success={success}")
        return result

    except Exception as e:
        error_msg = f"Unexpected error in job application email task: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}


def send_newsletter_subscription_emails(subscription_id):
    """
    Send email notifications for newsletter subscriptions using Mailtrap HTTP API

    Args:
        subscription_id (int): ID of the NewsletterSubscription object

    Returns:
        dict: Status of email sending with details
    """
    try:
        from users.models import NewsletterSubscription

        try:
            subscription = NewsletterSubscription.objects.get(id=subscription_id)
        except NewsletterSubscription.DoesNotExist:
            error_msg = f"NewsletterSubscription with ID {subscription_id} not found"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

        logger.info(f"Sending emails for newsletter subscription {subscription_id}")

        admin_sent = False
        subscriber_sent = False

        # Send admin notification
        try:
            admin_subject = f'New Newsletter Subscription - {subscription.email}'
            admin_message = render_to_string('users/emails/newsletter_admin.html', {
                'subscription': subscription
            })

            newsletter_email = getattr(settings, 'NEWSLETTER_EMAIL', 'news@mbuganiluxeadventures.com')

            admin_sent = send_email_via_mailtrap(
                subject=admin_subject,
                html_message=admin_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[newsletter_email],
            )

            if admin_sent:
                logger.info(f"Admin notification sent for newsletter subscription {subscription_id}")
            else:
                logger.error(f"Failed to send admin email for newsletter subscription {subscription_id}")

        except Exception as e:
            logger.error(f"Failed to send admin email for newsletter subscription {subscription_id}: {e}")

        # Send subscriber confirmation
        try:
            subscriber_subject = 'Welcome to Mbugani Luxe Adventures Newsletter!'
            subscriber_message = render_to_string('users/emails/newsletter_confirmation.html', {
                'subscription': subscription
            })

            subscriber_sent = send_email_via_mailtrap(
                subject=subscriber_subject,
                html_message=subscriber_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.email],
            )

            if subscriber_sent:
                logger.info(f"Subscriber confirmation sent for newsletter subscription {subscription_id}")
            else:
                logger.error(f"Failed to send subscriber email for newsletter subscription {subscription_id}")

        except Exception as e:
            logger.error(f"Failed to send subscriber email for newsletter subscription {subscription_id}: {e}")

        # Update subscription status
        try:
            subscription.admin_notification_sent = admin_sent
            subscription.confirmation_email_sent = subscriber_sent
            subscription.save()
        except Exception as e:
            logger.error(f"Failed to update newsletter subscription {subscription_id}: {e}")

        success = admin_sent and subscriber_sent
        result = {
            'success': success,
            'admin_sent': admin_sent,
            'subscriber_sent': subscriber_sent,
            'subscription_id': subscription_id,
            'timestamp': timezone.now().isoformat()
        }

        logger.info(f"Newsletter subscription emails completed for {subscription_id}: success={success}")
        return result

    except Exception as e:
        error_msg = f"Unexpected error in newsletter subscription email task: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}


def send_booking_confirmation_email(booking_id):
    """
    Send booking confirmation email using Mailtrap HTTP API

    Args:
        booking_id (int): ID of the Booking object

    Returns:
        dict: Status of email sending with details
    """
    try:
        from users.models import Booking

        try:
            booking = Booking.objects.get(id=booking_id)
        except Booking.DoesNotExist:
            error_msg = f"Booking with ID {booking_id} not found"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

        logger.info(f"Sending booking confirmation email for booking {booking_id}")

        # Prepare email context
        email_context = {
            'booking_id': booking.id,
            'full_name': booking.full_name,
            'package_name': booking.package.package_name,
            'number_of_adults': booking.number_of_adults,
            'number_of_children': booking.number_of_children or 0,
            'number_of_rooms': booking.number_of_rooms,
            'total_amount': booking.total_amount,
            'include_travelling': 'Yes' if booking.include_travelling else 'No',
        }

        # Email subject
        subject = f'Web Booking - Booking ID {booking.id}'

        # Render email body from template
        email_body = render_to_string('users/booking_confirmation.html', email_context)

        # Send email
        email_sent = send_email_via_mailtrap(
            subject=subject,
            html_message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['info@mbuganiluxeadventures.com'],
        )

        if email_sent:
            logger.info(f"Booking confirmation email sent for booking {booking_id}")
        else:
            logger.error(f"Failed to send booking confirmation email for booking {booking_id}")

        # Update booking status if needed
        try:
            booking.confirmation_email_sent = email_sent
            booking.save()
        except Exception as e:
            logger.error(f"Failed to update booking {booking_id}: {e}")

        result = {
            'success': email_sent,
            'booking_id': booking_id,
            'timestamp': timezone.now().isoformat()
        }

        return result

    except Exception as e:
        error_msg = f"Unexpected error in booking confirmation email task: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}
