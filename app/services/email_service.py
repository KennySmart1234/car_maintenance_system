import requests

from app.config.settings import settings


class EmailService:

    def send_notification_email(
        self,
        recipient: str,
        subject: str,
        body: str,
    ) -> None:

        data = {
            "Messages": [
                {
                    "From": {
                        "Email": settings.email_username,
                        "Name": "Motora Maintenance Service",
                    },
                    "To": [
                        {
                            "Email": recipient,
                        }
                    ],
                    "Subject": subject,
                    "TextPart": body,
                }
            ]
        }

        response = requests.post(
            "https://api.mailjet.com/v3.1/send",
            auth=(
                settings.mailjet_api_key,
                settings.mailjet_secret_key,
            ),
            json=data,
        )

        response.raise_for_status()

    def send_verification_email(
        self,
        recipient: str,
        verification_url: str,
    ) -> None:

        self.send_notification_email(
            recipient,
            "Verify your email address",
            "Hello,\n\n"
            "Thank you for registering with Motora Maintenance Service.\n\n"
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



    def send_password_reset_email(self, recipient: str, reset_url: str) -> None:

        self.send_notification_email(
            recipient,
            "Reset your Motora password",
            "Hello,\n\n"
            "We received a request to reset your Motora password.\n\n"
            "Please click the link below to reset your password:\n\n"
            f"{reset_url}\n\n"
            "This link will expire in 10 minutes.\n\n"
            "If you did not request a password reset, you can ignore this email.\n\n"
            "Motora Maintenance Service\n",
        )


