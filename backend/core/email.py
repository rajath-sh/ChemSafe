"""
ChemSafe IoT — Email Service

Handles sending email notifications via SMTP.
If SMTP is not configured, it falls back to logging the email to the console.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def is_configured() -> bool:
        """Check if SMTP variables are provided in the environment."""
        return bool(settings.SMTP_SERVER and settings.SMTP_USERNAME and settings.SMTP_PASSWORD)

    @staticmethod
    def send_email(to_email: str, subject: str, body: str) -> None:
        """
        Send an email using SMTP.
        If SMTP is not configured, simply log it to the console (Development Mode).
        """
        # Build the message
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = f"[ChemSafe] {subject}"
        msg.attach(MIMEText(body, "html"))

        if not EmailService.is_configured():
            # Development Mode Fallback
            border = "═" * 60
            mock_email = (
                f"\n{border}\n"
                f"📨 [DEV MODE] EMAIL DISPATCHED\n"
                f"To:      {to_email}\n"
                f"Subject: {msg['Subject']}\n"
                f"Body:\n{body}\n"
                f"{border}\n"
            )
            logger.info(mock_email)
            return

        # Real SMTP Dispatch
        try:
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            logger.info("Successfully sent email to %s: %s", to_email, subject)
        except Exception as e:
            logger.error("Failed to send email to %s. Error: %s", to_email, str(e))
