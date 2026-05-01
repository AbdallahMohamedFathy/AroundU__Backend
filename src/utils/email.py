"""
Email utilities for sending verification and password reset emails
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import socket
from src.core.config import settings
from src.core.logger import logger

# Force IPv4 to fix "Network is unreachable" error on Railway
def _force_ipv4():
    old_getaddrinfo = socket.getaddrinfo
    def new_getaddrinfo(*args, **kwargs):
        responses = old_getaddrinfo(*args, **kwargs)
        return [response for response in responses if response[0] == socket.AF_INET]
    socket.getaddrinfo = new_getaddrinfo

def send_email(
    to_email: str,
    subject: str,
    body_html: str,
    body_text: Optional[str] = None
) -> bool:
    """
    Send an email using Gmail SMTP SSL (Port 465).
    """
    logger.info(f"[EMAIL] Attempting to send email to {to_email}")

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("[EMAIL] SMTP credentials not configured. Email not sent.")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
        msg['To'] = to_email

        if body_text:
            msg.attach(MIMEText(body_text, 'plain'))
        msg.attach(MIMEText(body_html, 'html'))

        # Force port 465 for SSL (bypasses some Railway blocks)
        port = 465 
        logger.info(f"[EMAIL] Connecting to SMTP server {settings.SMTP_HOST}:{port} (SSL)...")
        _force_ipv4()
        
        # Use SMTP_SSL instead of SMTP + starttls
        with smtplib.SMTP_SSL(settings.SMTP_HOST, port) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info(f"[EMAIL] Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"[EMAIL] FAILED to send email to {to_email}: {str(e)}")
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
            <h2>Welcome to AroundU, {user_name}!</h2>
            <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
            <a href="{verification_link}" class="button">Verify Email Address</a>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all;">{verification_link}</p>
            <p>This link will expire in 24 hours.</p>
            <div class="footer">
                <p>If you didn't create an account with AroundU, please ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    Welcome to AroundU, {user_name}!

    Thank you for registering. Please verify your email address by clicking the link below:

    {verification_link}

    This link will expire in 24 hours.

    If you didn't create an account with AroundU, please ignore this email.
    """

    return send_email(
        to_email=email,
        subject="Verify your AroundU account",
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
        subject="Reset your AroundU password",
        body_html=html_body,
        body_text=text_body
    )
