import smtplib
from email.message import EmailMessage

from app.config.database import settings


class EmailService:

    def send_verification_email(self, recipient: str, verification_url: str):
        message = EmailMessage()

        message["Subject"] = "Verify your email address"
        message["From"] = settings.email_username
        message["To"] = recipient

        message.set_content(
            f"""
Hello,

Thank you for registering with KennySmart -> Car Maintenance Service.

Please click the link below to verify your email address:

{verification_url}

If you did not create this account, you can ignore this email.
"""
        )

        with smtplib.SMTP(settings.email_host, settings.email_port) as server:
            server.starttls()
            server.login(settings.email_username, settings.email_password)
            server.send_message(message)