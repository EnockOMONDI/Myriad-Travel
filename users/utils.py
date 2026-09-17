from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


class TokenGenerator(PasswordResetTokenGenerator):
	pass

generate_token=TokenGenerator()





def send_booking_confirmation_email(booking):
    """
    Send booking confirmation email synchronously using Mailtrap HTTP API
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        from users.tasks import send_booking_confirmation_email as send_email_task

        # Send email synchronously
        result = send_email_task(booking.id)

        if result.get('success'):
            logger.info(f"Booking confirmation email sent successfully: booking_id={booking.id}")
            return True
        else:
            logger.error(f"Failed to send booking confirmation email for {booking.id}")
            return False

    except Exception as e:
        logger.error(f"Failed to send booking confirmation email for {booking.id}: {e}")
        return False