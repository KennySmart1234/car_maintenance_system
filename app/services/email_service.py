import smtplib
from email.message import EmailMessage

from app.config.settings import settings

SMTP_TIMEOUT_SECONDS = 10


class EmailService:

    def _send(self, message: EmailMessage) -> None:
        with smtplib.SMTP(
            settings.email_host,
            settings.email_port,
            timeout=SMTP_TIMEOUT_SECONDS,
        ) as server:
            server.starttls()
            server.login(settings.email_username, settings.email_password)
            server.send_message(message)

    def send_notification_email(self, recipient: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.email_username
        message["To"] = recipient
        message.set_content(body)
        self._send(message)

    def send_verification_email(self, recipient: str, verification_url: str) -> None:
        self.send_notification_email(
            recipient,
            "Verify your email address",
            "Hello,\n\n"
            "Thank you for registering with the Car Maintenance System.\n\n"
            "Please click the link below to verify your email address:\n\n"
            f"{verification_url}\n\n"
            "If you did not create this account, you can ignore this email.\n",
        )

    def send_additional_maintenance_email(
        self,
        recipient: str,
        customer_name: str,
        request_id: str,
        maintenance_service_id: str,
        service_name: str,
        description: str,
        cost: str,
    ) -> None:
        self.send_notification_email(
            recipient,
            "Additional Maintenance Requires Your Approval",
            f"Hello {customer_name},\n\n"
            "During the inspection of your vehicle, the workshop identified\n"
            "additional maintenance that requires your approval.\n\n"
            f"Maintenance Request ID: {request_id}\n"
            f"Maintenance Service ID: {maintenance_service_id}\n"
            f"Service: {service_name}\n"
            f"Description: {description}\n"
            f"Estimated Cost: {cost}\n\n"
            "Please log in to the Car Maintenance System, review the\n"
            "additional service details, and approve or reject the work\n"
            "before the workshop proceeds.\n\n"
            "Car Maintenance System\n",
        )