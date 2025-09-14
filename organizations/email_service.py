from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class CoordinatorEmailService:
    """Service for sending coordinator-related emails"""

    @staticmethod
    def get_system_url(request=None):
        """Get the system URL for email templates"""
        if request:
            return f"{request.scheme}://{request.get_host()}"
        return "http://localhost:8000"  # Fallback for console/testing

    @staticmethod
    def send_welcome_email(coordinator, organization, request=None):
        """Send welcome email to new coordinator"""
        try:
            subject = f"Welcome to PRE System - {organization.name} Coordinator"

            context = {
                'coordinator': coordinator,
                'organization': organization,
                'system_url': CoordinatorEmailService.get_system_url(request),
            }

            # Render HTML and text versions
            html_message = render_to_string('emails/coordinator_welcome.html', context)
            text_message = render_to_string('emails/coordinator_welcome.txt', context)

            # Send email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[coordinator.email],
                html_message=html_message,
                fail_silently=False
            )

            logger.info(f"Welcome email sent to coordinator: {coordinator.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send welcome email to {coordinator.email}: {str(e)}")
            return False

    @staticmethod
    def send_update_notification(coordinator, organization, request=None):
        """Send notification email when coordinator details are updated"""
        try:
            subject = f"Account Information Updated - PRE System"

            context = {
                'coordinator': coordinator,
                'organization': organization,
                'system_url': CoordinatorEmailService.get_system_url(request),
            }

            # Render HTML and text versions
            html_message = render_to_string('emails/coordinator_updated.html', context)
            text_message = render_to_string('emails/coordinator_updated.txt', context)

            # Send email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[coordinator.email],
                html_message=html_message,
                fail_silently=False
            )

            logger.info(f"Update notification sent to coordinator: {coordinator.email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send update notification to {coordinator.email}: {str(e)}")
            return False