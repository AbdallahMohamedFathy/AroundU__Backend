"""
Email utilities for sending verification and password reset emails
"""
import requests
from typing import Optional
from src.core.config import settings
from src.core.logger import logger

def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None
) -> bool:
    """
    Send an email using Brevo (Sendinblue) HTTP API to bypass Railway SMTP blocks.
    """
    logger.info(f"[EMAIL] Attempting to send email to {to_email} via Brevo API")

    if not settings.BREVO_API_KEY:
        logger.warning("[EMAIL] BREVO_API_KEY not configured. Email not sent.")
        return False

    try:
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "content-type": "application/json"
        }
        
        payload = {
            "sender": {
                "name": settings.EMAILS_FROM_NAME,
                "email": settings.EMAILS_FROM_EMAIL
            },
            "to": [
                {
                    "email": to_email
                }
            ],
            "subject": subject,
            "htmlContent": body_html
        }
        
        if body_text:
            payload["textContent"] = body_text

        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code in [200, 201]:
            logger.info(f"[EMAIL] Email sent successfully to {to_email}")
            return True
        else:
            logger.error(f"[EMAIL] Brevo API FAILED: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"[EMAIL] Request to Brevo FAILED: {str(e)}")
        return False





def send_verification_email(email: str, token: str, user_name: str) -> bool:
    """
    Send email verification link to user.

    Args:
        email: User's email address
        token: Verification token
        user_name: User's full name

    Returns:
        True if email sent successfully
    """
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin: 20px 0;
            }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- App Logo -->
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="https://7waleek.com/logo.jpeg" alt="7waleek Logo" style="max-width: 150px; height: auto;" />
            </div>
            <h2>Welcome to 7waleek, {user_name}!</h2>
            <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
            <a href="{verification_link}" class="button">Verify Email Address</a>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all;">{verification_link}</p>
            <p>This link will expire in 24 hours.</p>
            <div class="footer">
                <p>If you didn't create an account with 7waleek, please ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    Welcome to 7waleek, {user_name}!

    Thank you for registering. Please verify your email address by clicking the link below:

    {verification_link}

    This link will expire in 24 hours.

    If you didn't create an account with 7waleek, please ignore this email.
    """

    return send_email(
        to_email=email,
        subject="Verify your 7waleek account",
        body_html=html_body,
        body_text=text_body
    )


def send_password_reset_email(email: str, token: str, user_name: str) -> bool:
    """
    Send password reset link to user.

    Args:
        email: User's email address
        token: Password reset token
        user_name: User's full name

    Returns:
        True if email sent successfully
    """
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #2196F3;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin: 20px 0;
            }}
            .warning {{
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                padding: 12px;
                border-radius: 4px;
                margin: 20px 0;
            }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- App Logo -->
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="https://res.cloudinary.com/dvecsfbmu/image/upload/v1777668197/WhatsApp_Image_2026-05-01_at_11.32.59_PM_rti73a.jpg" alt="7waleek Logo" style="max-width: 150px; height: auto;" />
            </div>
            <h2>Password Reset Request</h2>
            <p>Hello {user_name},</p>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            <a href="{reset_link}" class="button">Reset Password</a>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all;">{reset_link}</p>
            <div class="warning">
                <strong>Security Notice:</strong> This link will expire in 1 hour for security reasons.
            </div>
            <div class="footer">
                <p>If you didn't request a password reset, please ignore this email and your password will remain unchanged.</p>
                <p>For security concerns, please contact our support team.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    Password Reset Request

    Hello {user_name},

    We received a request to reset your password. Click the link below to create a new password:

    {reset_link}

    This link will expire in 1 hour for security reasons.

    If you didn't request a password reset, please ignore this email and your password will remain unchanged.
    """

    return send_email(
        to_email=email,
        subject="Reset your 7waleek password",
        body_html=html_body,
        body_text=text_body
    )
