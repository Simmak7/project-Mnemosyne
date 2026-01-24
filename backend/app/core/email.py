"""
Email service using Resend.

Provides email sending functionality for password reset, security alerts, etc.
"""

import logging
from typing import Optional
import httpx

from core import config

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Resend API."""

    def __init__(self):
        self.api_key = config.RESEND_API_KEY
        self.from_address = config.EMAIL_FROM_ADDRESS
        self.from_name = config.EMAIL_FROM_NAME
        self.api_url = "https://api.resend.com/emails"

    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(self.api_key and self.api_key != "")

    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via Resend API.

        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)

        Returns:
            True if email was sent successfully
        """
        if not self.is_configured():
            logger.warning("Email service not configured (RESEND_API_KEY missing)")
            return False

        payload = {
            "from": f"{self.from_name} <{self.from_address}>",
            "to": [to],
            "subject": subject,
            "html": html_content
        }

        if text_content:
            payload["text"] = text_content

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 200:
                    logger.info(f"Email sent successfully to {to}")
                    return True
                else:
                    logger.error(
                        f"Failed to send email: {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    async def send_password_reset_email(
        self,
        to: str,
        username: str,
        reset_token: str
    ) -> bool:
        """
        Send a password reset email.

        Args:
            to: Recipient email address
            username: User's username
            reset_token: Password reset token

        Returns:
            True if email was sent successfully
        """
        reset_url = f"{config.FRONTEND_URL}/reset-password?token={reset_token}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 8px 8px 0 0; }}
                .header h1 {{ color: white; margin: 0; font-size: 24px; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
                .footer {{ color: #6c757d; font-size: 12px; margin-top: 20px; }}
                .warning {{ color: #dc3545; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <p>Hi <strong>{username}</strong>,</p>
                    <p>You requested to reset your password for your Mnemosyne account. Click the button below to set a new password:</p>
                    <a href="{reset_url}" class="button">Reset Password</a>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #667eea;">{reset_url}</p>
                    <p class="warning">This link will expire in {config.PASSWORD_RESET_EXPIRE_MINUTES} minutes.</p>
                    <p>If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                    <div class="footer">
                        <p>This email was sent by Mnemosyne</p>
                        <p>If you have questions, please contact support.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Hi {username},

        You requested to reset your password for your Mnemosyne account.

        Click the link below to set a new password:
        {reset_url}

        This link will expire in {config.PASSWORD_RESET_EXPIRE_MINUTES} minutes.

        If you didn't request this password reset, you can safely ignore this email.

        - Mnemosyne Team
        """

        return await self.send_email(
            to=to,
            subject="Reset Your Mnemosyne Password",
            html_content=html_content,
            text_content=text_content
        )

    async def send_security_alert_email(
        self,
        to: str,
        username: str,
        alert_type: str,
        details: str
    ) -> bool:
        """
        Send a security alert email.

        Args:
            to: Recipient email address
            username: User's username
            alert_type: Type of security alert
            details: Alert details

        Returns:
            True if email was sent successfully
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc3545; padding: 30px; border-radius: 8px 8px 0 0; }}
                .header h1 {{ color: white; margin: 0; font-size: 24px; }}
                .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
                .alert-box {{ background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 6px; margin: 20px 0; }}
                .footer {{ color: #6c757d; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Security Alert</h1>
                </div>
                <div class="content">
                    <p>Hi <strong>{username}</strong>,</p>
                    <p>We detected a security-related activity on your Mnemosyne account:</p>
                    <div class="alert-box">
                        <strong>{alert_type}</strong>
                        <p>{details}</p>
                    </div>
                    <p>If this was you, no action is needed. If you didn't perform this action, please secure your account immediately by changing your password.</p>
                    <div class="footer">
                        <p>This email was sent by Mnemosyne</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        return await self.send_email(
            to=to,
            subject=f"Security Alert: {alert_type}",
            html_content=html_content
        )


# Singleton instance
email_service = EmailService()


# ============================================
# Phase 2: Account Management Email Functions
# ============================================

def send_email_change_verification(
    to_email: str,
    username: str,
    token: str
) -> None:
    """
    Send email change verification (sync wrapper).
    Note: Email service is async but services call synchronously.
    In production, queue this as a Celery task.
    """
    verify_url = f"{config.FRONTEND_URL}/verify-email-change?token={token}"
    logger.info(f"Email change verification URL generated for {username}: {verify_url}")
    # In production: send via Celery task
    # For now, log the URL for manual testing


def send_email_changed_notification(
    to_email: str,
    username: str,
    new_email: str
) -> None:
    """
    Send notification to old email about email change.
    """
    logger.info(f"Email changed notification for {username}: old={to_email}, new={new_email}")
    # In production: send via Celery task


def send_account_deletion_confirmation(
    to_email: str,
    username: str,
    deletion_date
) -> None:
    """
    Send account deletion confirmation.
    """
    restore_url = f"{config.FRONTEND_URL}/restore-account"
    logger.info(
        f"Account deletion scheduled for {username}. "
        f"Permanent deletion: {deletion_date}. Restore at: {restore_url}"
    )
    # In production: send via Celery task
