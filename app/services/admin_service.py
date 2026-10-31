from datetime import datetime, date, timezone
from uuid import UUID

from sqlmodel import Session

from app.config.password import hash_password
from app.enums.email_status import EmailStatus
from app.enums.user_role import UserRole
from app.exceptions.app_exception import AppException
from app.enums.image_category import ImageCategory
from app.models import EmailNotification, User
from app.models.maintenance_image import MaintenanceImage
from app.enums.maintenance_status import MaintenanceStatus
from app.models.payment import Payment
from app.repositories.car_repository import CarRepository
from app.repositories.email_notification_repository import EmailNotificationRepository
from app.repositories.maintenance_image_repository import MaintenanceImageRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate
from app.services import image_storage
from app.services.admin_view_service import build_admin_request_response
from app.services.email_service import EmailService

from app.services.maintenance_request_service import MaintenanceRequestService
from app.services.maintenance_service_service import MaintenanceServiceService
from app.services.payment_service import PaymentService
from app.repositories.maintenance_request_repository import MaintenanceRequestRepository
from app.schemas.admin_schema import EmailNotificationResponse



class AdminService:
    def __init__(self, session: Session):
        self.car_repository = CarRepository(session)
        self.maintenance_request_service = MaintenanceRequestService(session)
        self.maintenance_request_repository = MaintenanceRequestRepository(session)
        self.maintenance_service_service = MaintenanceServiceService(session)
        self.image_repository = MaintenanceImageRepository(session)
        self.payment_service = PaymentService(session)
        self.user_repository = UserRepository(session)
        self.email_notification_repository = EmailNotificationRepository(session)
        self.email_service = EmailService()

    def add_admin(self, user_data: UserCreate):
        existing_user = self.user_repository.find_by_email(user_data.email)

        if existing_user is not None:
            raise AppException("Email already exists", status_code=400)

        admin = User(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
            password=hash_password(user_data.password),
            role=UserRole.WORKSHOP_ADMIN,
            email_verified=True,
        )

        return self.user_repository.create(admin)

    def list_admins(self) -> list[User]:
        return self.user_repository.find_by_role(UserRole.WORKSHOP_ADMIN)


    def get_all_maintenance_requests(
            self,
            status: MaintenanceStatus | None = None,
    ):
        requests = self.maintenance_request_repository.find_all(status)

        responses = []

        for request in requests:
            vehicle = self.car_repository.find_by_id(request.car_id)

            if vehicle is None:
                continue

            customer = self.user_repository.find_by_id(vehicle.customer_id)

            if customer is None:
                continue

            response = build_admin_request_response(request, vehicle, customer)

            responses.append(response)

        return responses



    @staticmethod
    def _normalize_plate(value: str) -> str:
        return "".join(value.split()).replace("-", "").upper()

    @staticmethod
    def _normalize_vin(value: str) -> str:
        return "".join(value.split()).upper()

    def check_vehicle(self, car_id: UUID, plate_number: str, vin: str) -> dict:
        """Compare what the admin sees on the car with what is on record and
        say which of the two values (if any) differs."""
        if not plate_number or not plate_number.strip():
            raise AppException("Plate number is required", status_code=400)

        if not vin or not vin.strip():
            raise AppException("VIN is required", status_code=400)

        car = self.car_repository.find_by_id(car_id)

        if car is None:
            return {
                "verified": False,
                "car_found": False,
                "plate_number_matches": False,
                "vin_matches": False,
            }

        plate_matches = (
            self._normalize_plate(car.plate_number)
            == self._normalize_plate(plate_number)
        )
        vin_matches = self._normalize_vin(car.vin) == self._normalize_vin(vin)

        return {
            "verified": plate_matches and vin_matches,
            "car_found": True,
            "plate_number_matches": plate_matches,
            "vin_matches": vin_matches,
        }

    def verify_vehicle(self, car_id: UUID, plate_number: str, vin: str) -> bool:
        return self.check_vehicle(car_id, plate_number, vin)["verified"]


    def accept_request(self, request_id: UUID):
        return self.maintenance_request_service.update_status(
            request_id, MaintenanceStatus.ACCEPTED)


    def inspect_car(self, request_id: UUID, notes: str | None = None):
        request = self.maintenance_request_service.update_status(
            request_id,
            MaintenanceStatus.INSPECTING,
        )

        if notes is not None and notes.strip():
            return self._save_inspection_notes(request, notes)

        return request

    def set_inspection_notes(self, request_id: UUID, notes: str):
        request = self.maintenance_request_service.get_request_by_id(request_id)

        if request.status not in (
            MaintenanceStatus.INSPECTING,
            MaintenanceStatus.AWAITING_APPROVAL,
        ):
            raise AppException(
                "Inspection notes can only be edited while inspecting "
                "or awaiting approval"
            )

        return self._save_inspection_notes(request, notes)

    def _save_inspection_notes(self, request, notes: str):
        request.inspection_notes = notes.strip()
        request.inspected_at = datetime.now(timezone.utc)
        return self.maintenance_request_repository.update(request)

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

    def upload_image_file(
        self, request_id: UUID, category: ImageCategory, content: bytes
    ) -> MaintenanceImage:
        """Store an actual photo file and attach it to the request."""
        self.maintenance_request_service.get_request_by_id(request_id)

        image_url = image_storage.save_image(content)

        try:
            return self.image_repository.create(
                MaintenanceImage(
                    maintenance_request_id=request_id,
                    image_url=image_url,
                    category=category,
                )
            )
        except Exception:
            image_storage.delete_image_file(image_url)
            raise

    def update_image_category(
        self, image_id: UUID, category: ImageCategory
    ) -> MaintenanceImage:
        image = self.image_repository.find_by_id(image_id)

        if image is None:
            raise AppException("Image not found", status_code=404)

        image.category = category
        image.updated_at = datetime.now(timezone.utc)
        return self.image_repository.update(image)

    def list_notifications(
        self, status: EmailStatus = EmailStatus.FAILED
    ) -> list[EmailNotificationResponse]:
        responses = []

        for notification in self.email_notification_repository.find_by_status(status):
            user = self.user_repository.find_by_id(notification.user_id)

            responses.append(
                EmailNotificationResponse(
                    id=notification.id,
                    user_id=notification.user_id,
                    recipient_email=user.email if user else None,
                    maintenance_request_id=notification.maintenance_request_id,
                    title=notification.title,
                    subject=notification.subject,
                    status=notification.status,
                    sent_at=notification.sent_at,
                )
            )

        return responses

    def _retry_notification(self, notification: EmailNotification) -> bool:
        user = self.user_repository.find_by_id(notification.user_id)

        if user is None:
            return False

        try:
            self.email_service.send_notification_email(
                user.email, notification.subject, notification.message
            )
        except Exception as error:
            print("EMAIL ERROR:", error)
            return False

        notification.status = EmailStatus.SENT
        notification.sent_at = datetime.now(timezone.utc)
        self.email_notification_repository.update(notification)
        return True

    def retry_failed_notifications(self) -> dict:
        sent = 0
        still_failed = 0

        for notification in self.email_notification_repository.find_failed():
            if self._retry_notification(notification):
                sent += 1
            else:
                still_failed += 1

        return {"sent": sent, "still_failed": still_failed}

    def retry_notification(self, notification_id: UUID) -> EmailNotificationResponse:
        notification = self.email_notification_repository.find_by_id(notification_id)

        if notification is None:
            raise AppException("Notification not found", status_code=404)

        if notification.status != EmailStatus.FAILED:
            raise AppException("Only failed notifications can be retried")

        self._retry_notification(notification)

        user = self.user_repository.find_by_id(notification.user_id)
        return EmailNotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            recipient_email=user.email if user else None,
            maintenance_request_id=notification.maintenance_request_id,
            title=notification.title,
            subject=notification.subject,
            status=notification.status,
            sent_at=notification.sent_at,
        )

    def record_payment(self, payment: Payment):
        return self.payment_service.create_payment(payment)


    def set_next_service(self, request_id: UUID, date: date):
        return self.maintenance_request_service.update_next_service_date(request_id, date)


