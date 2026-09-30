"""Email verification module using the configured HTTP email provider."""
from django.conf import settings
import logging
from users.tasks import send_email_via_mailtrap

logger = logging.getLogger(__name__)


def verification_mail(link, user):
    """
    Send account verification email using Mailtrap HTTP API

    Args:
        link (str): Verification link URL
        user (User): Django user object

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        logger.info(f"Sending verification email to {user.email}")

        # Build email HTML content
        message = f'Hi {user.username}, welcome to Myriad Travel.<br>To activate your account, click the link below:<br><a href="{link}">Activate Account</a><br><br>'

        directors_message = """
        <p><strong>Directors message</strong></p>
        """

        advantages_message = """
        <p>We are delighted to have you as part of the Myriad Travel community. Our goal is simple: every trip should feel well planned, memorable, and effortless. Our team handles the details so you can focus on the experience.</p>
        """

        html_content = message + directors_message + advantages_message

        sent = send_email_via_mailtrap(
            subject="Welcome to Myriad Travel",
            html_message=html_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'Myriad Travel <info@myriad-travel.com>'),
            recipient_list=[user.email],
        )
        if sent:
            logger.info(f"Verification email sent successfully to {user.email}")
        return sent

    except Exception as e:
        logger.error(f"Error sending verification email to {user.email}: {e}")
        return False



