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
        message = EmailMessage()

        message["Subject"] = "Additional Maintenance Requires Your Approval"
        message["From"] = settings.email_username
        message["To"] = recipient

        message.set_content(
            f"""
    Hello {customer_name},

    During the inspection of your vehicle, the workshop identified
    additional maintenance that requires your approval.

    Maintenance Request ID: {request_id}
    Maintenance Service ID: {maintenance_service_id}
    Service: {service_name}
    Description: {description}
    Estimated Cost: {cost}

    Please log in to the Car Maintenance System, review the
    additional service details, and approve or reject the work
    before the workshop proceeds.

    Car Maintenance System
    """
        )

        with smtplib.SMTP(settings.email_host, settings.email_port) as server:
            server.starttls()
            server.login(settings.email_username, settings.email_password)
            server.send_message(message)

