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
            raise AppException("Plate number is required")

        if not vin or not vin.strip():
            raise AppException("VIN is required")

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
        request = None


        if service.is_additional:
            request = self.maintenance_request_service.get_request_by_id(
                service.maintenance_request_id
            )

            if request.status not in [
                MaintenanceStatus.INSPECTING,
                MaintenanceStatus.AWAITING_APPROVAL,
            ]:
                raise AppException(
                    "Additional services can only be added while inspecting "
                    "or awaiting approval"
                )

        created_service = self.maintenance_service_service.create_service(service)


        if (
                created_service.is_additional
                and request.status == MaintenanceStatus.INSPECTING
        ):
            self.maintenance_request_service.update_status(
                created_service.maintenance_request_id,
                MaintenanceStatus.AWAITING_APPROVAL,
            )


        if created_service.is_additional:
            maintenance_request = self.maintenance_request_service.get_request_by_id(
                created_service.maintenance_request_id
            )

            car = self.car_repository.find_by_id(maintenance_request.car_id)

            if car is None:
                raise AppException("Car not found")

            customer = self.user_repository.find_by_id(car.customer_id)

            if customer is None:
                raise AppException("Customer not found")

            notification = EmailNotification(
                user_id=customer.id,
                maintenance_request_id=maintenance_request.id,
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
                    request_id=str(maintenance_request.id),
                    maintenance_service_id=str(created_service.id),
                    service_name=created_service.name,
                    description=created_service.description,
                    cost=str(created_service.cost),
                )

                notification.status = EmailStatus.SENT
                notification.sent_at = datetime.now(timezone.utc)
                self.email_notification_repository.update(notification)

                return {
                    "message": "Email sent successfully.",
                    "maintenance_service_id": str(created_service.id),
                }


            except Exception as e:

                notification.status = EmailStatus.FAILED

                self.email_notification_repository.update(notification)

                print("EMAIL ERROR:", e)

                raise AppException(

                    "Additional service was saved, but the email could not be sent."

                )



    def update_status(self, request_id: UUID, status: MaintenanceStatus):
        return self.maintenance_request_service.update_status(
            request_id, status)

    def upload_image(self, image: MaintenanceImage):
        return self.image_repository.create(image)


    def record_payment(self, payment: Payment):
        return self.payment_service.create_payment(payment)

    def set_next_service(self, request_id: UUID, date: date):
        return self.maintenance_request_service.update_next_service_date(request_id, date)