from datetime import datetime, date, timezone
from uuid import UUID

from sqlmodel import Session

from app.enums.email_status import EmailStatus
from app.exceptions.app_exception import AppException
from app.models import EmailNotification
from app.models.maintenance_image import MaintenanceImage
from app.enums.maintenance_status import MaintenanceStatus
from app.models.payment import Payment
from app.repositories.car_repository import CarRepository
from app.repositories.email_notification_repository import EmailNotificationRepository
from app.repositories.maintenance_image_repository import MaintenanceImageRepository
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService

from app.services.maintenance_request_service import MaintenanceRequestService
from app.services.maintenance_service_service import MaintenanceServiceService
from app.services.payment_service import PaymentService


class AdminService:
    def __init__(self, session: Session):
        self.car_repository = CarRepository(session)
        self.maintenance_request_service = MaintenanceRequestService(session)
        self.maintenance_service_service = MaintenanceServiceService(session)
        self.image_repository = MaintenanceImageRepository(session)
        self.payment_service = PaymentService(session)
        self.user_repository = UserRepository(session)
        self.email_notification_repository = EmailNotificationRepository(session)
        self.email_service = EmailService()


    def verify_vehicle(self, car_id: UUID, plate_number: str, vin: str) -> bool:
        if not plate_number or not plate_number.strip():
            raise AppException("Plate number is required", status_code=400)

        if not vin or not vin.strip():
            raise AppException("VIN is required", status_code=400)

        car = self.car_repository.find_by_id(car_id)

        if car is None:
            return False

        return (
                car.plate_number == plate_number
                and car.vin == vin
        )


    def accept_request(self, request_id: UUID):
        return self.maintenance_request_service.update_status(
            request_id, MaintenanceStatus.ACCEPTED)


    def inspect_car(self, request_id: UUID):
        return self.maintenance_request_service.update_status(
            request_id,
            MaintenanceStatus.INSPECTING,
        )

    def add_service(self, service):
        request = self.maintenance_request_service.get_request_by_id(
            service.maintenance_request_id
        )

        if request.status in (MaintenanceStatus.COMPLETED, MaintenanceStatus.CANCELED):
            raise AppException(
                "Services cannot be added to a completed or canceled request"
            )

        customer = None

        if service.is_additional:
            if request.status not in [
                MaintenanceStatus.INSPECTING,
                MaintenanceStatus.AWAITING_APPROVAL,
            ]:
                raise AppException(
                    "Additional services can only be added while inspecting "
                    "or awaiting approval"
                )

            # Look these up BEFORE saving, so a failure leaves nothing half-done.
            car = self.car_repository.find_by_id(request.car_id)
            if car is None:
                raise AppException("Car not found", status_code=404)

            customer = self.user_repository.find_by_id(car.customer_id)
            if customer is None:
                raise AppException("Customer not found", status_code=404)

        created_service = self.maintenance_service_service.create_service(service)

        if not created_service.is_additional:
            return {
                "message": "Service added.",
                "maintenance_service_id": str(created_service.id),
                "email_sent": False,
            }

        if request.status == MaintenanceStatus.INSPECTING:
            self.maintenance_request_service.update_status(
                request.id,
                MaintenanceStatus.AWAITING_APPROVAL,
            )

        email_sent = self._notify_customer_of_additional_service(
            customer, request, created_service
        )

        return {
            "message": (
                "Service added and customer notified."
                if email_sent
                else "Service added, but the email could not be sent."
            ),
            "maintenance_service_id": str(created_service.id),
            "email_sent": email_sent,
        }

    def _notify_customer_of_additional_service(self, customer, request, created_service) -> bool:
        notification = EmailNotification(
            user_id=customer.id,
            maintenance_request_id=request.id,
            title="Additional maintenance requires your approval",
            subject="Additional Maintenance Requires Your Approval",
            message=(
                f"Additional service: {created_service.name}. "
                f"Description: {created_service.description}. "
                f"Estimated cost: {created_service.cost}. "
                "Please review your dashboard and approve or reject "
                "this service before the workshop proceeds."
            ),
            status=EmailStatus.PENDING,
        )
        notification = self.email_notification_repository.create(notification)

        try:
            self.email_service.send_additional_maintenance_email(
                recipient=customer.email,
                customer_name=f"{customer.first_name} {customer.last_name}",
                request_id=str(request.id),
                maintenance_service_id=str(created_service.id),
                service_name=created_service.name,
                description=created_service.description,
                cost=str(created_service.cost),
            )
        except Exception as error:
            print("EMAIL ERROR:", error)
            notification.status = EmailStatus.FAILED
            self.email_notification_repository.update(notification)
            return False

        notification.status = EmailStatus.SENT
        notification.sent_at = datetime.now(timezone.utc)
        self.email_notification_repository.update(notification)
        return True

    def update_status(self, request_id: UUID, status: MaintenanceStatus):
        return self.maintenance_request_service.update_status(
            request_id, status)

    def upload_image(self, image: MaintenanceImage):
        self.maintenance_request_service.get_request_by_id(
            image.maintenance_request_id
        )
        return self.image_repository.create(image)

    def retry_failed_notifications(self) -> dict:
        sent = 0
        still_failed = 0

        for notification in self.email_notification_repository.find_failed():
            user = self.user_repository.find_by_id(notification.user_id)

            if user is None:
                still_failed += 1
                continue

            try:
                self.email_service.send_notification_email(
                    user.email, notification.subject, notification.message
                )
            except Exception as error:
                print("EMAIL ERROR:", error)
                still_failed += 1
                continue

            notification.status = EmailStatus.SENT
            notification.sent_at = datetime.now(timezone.utc)
            self.email_notification_repository.update(notification)
            sent += 1

        return {"sent": sent, "still_failed": still_failed}

    def record_payment(self, payment: Payment):
        return self.payment_service.create_payment(payment)

    def set_next_service(self, request_id: UUID, date: date):
        return self.maintenance_request_service.update_next_service_date(request_id, date)