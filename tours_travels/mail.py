"""
Email verification module using Mailtrap HTTP API
"""
from django.conf import settings
from mailtrap import Mail, Address, MailtrapClient
import logging

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

        # Initialize Mailtrap client
        client = MailtrapClient(token=settings.MAILTRAP_API_TOKEN)

        # Build email HTML content
        message = f'Hi {user.username}, welcome to Mbugani Luxe Adventures.<br>To activate your account, click the link below:<br><a href="{link}">Activate Account</a><br><br>'

        directors_message = """
        <p><strong>Directors message</strong></p>
        """

        advantages_message = """
        <p>We are delighted to have you as part of the Mbugani Luxe Adventures community. Our goal is simple: We want every trip you take with us to be <strong>affordable</strong> and wonderfully <strong>memorable</strong>. That's where we come in, we take care of all the little things to ensure your journey is smooth and effortless, creating moments you'll treasure forever.</p>
        """

        html_content = message + directors_message + advantages_message

        # Create mail object
        mail = Mail(
            sender=Address(email="info@mbuganiluxeadventures.com", name="Mbugani Luxe Adventures"),
            to=[Address(email=user.email)],
            subject="Welcome to Mbugani Luxe Adventures",
            html=html_content,
        )

        # Send email
        response = client.send(mail)

        logger.info(f"Verification email sent successfully to {user.email}: {response}")
        return True

    except Exception as e:
        logger.error(f"Error sending verification email to {user.email}: {e}")
        return False



