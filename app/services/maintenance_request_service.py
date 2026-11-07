from app.enums.email_status import EmailStatus
from app.models import EmailNotification
from app.repositories.user_repository import UserRepository
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlmodel import Session

from app.enums.approval_status import ApprovalStatus
from app.enums.maintenance_status import MaintenanceStatus
from app.exceptions.app_exception import AppException
from app.models.maintenance_request import MaintenanceRequest
from app.repositories.car_repository import CarRepository
from app.repositories.email_notification_repository import EmailNotificationRepository
from app.repositories.maintenance_request_repository import MaintenanceRequestRepository
from app.repositories.maintenance_service_repository import MaintenanceServiceRepository
from app.repositories.payment_repository import PaymentRepository



class MaintenanceRequestService:
    def __init__(self, session: Session):
        self.car_repository = CarRepository(session)
        self.maintenance_request_repository = MaintenanceRequestRepository(session)
        self.maintenance_service_repository = MaintenanceServiceRepository(session)
        self.payment_repository = PaymentRepository(session)
        self.user_repository = UserRepository(session)
        self.email_notification_repository = EmailNotificationRepository(session)
        self.notification_service = NotificationService(session)
        self.email_service = EmailService()


    def _notify_status(self, request_id: UUID, status: MaintenanceStatus) -> None:
        service = getattr(self, "notification_service", None)

        if service is not None:
            service.notify_status_change(request_id, status)

        try:
            request = self.maintenance_request_repository.find_by_id(request_id)

            if request is None:
                return

            car = self.car_repository.find_by_id(request.car_id)

            if car is None:
                return

            customer = self.user_repository.find_by_id(car.customer_id)

            if customer is None:
                return

            status_messages = {
                MaintenanceStatus.ACCEPTED: (
                    "Your maintenance request has been accepted by our team."
                ),
                MaintenanceStatus.INSPECTING: (
                    "We have started inspecting your vehicle."
                ),
                MaintenanceStatus.AWAITING_APPROVAL: (
                    "Additional maintenance requires your approval "
                    "before work can continue."
                ),
                MaintenanceStatus.IN_PROGRESS: (
                    "Work on your vehicle has started."
                ),
                MaintenanceStatus.COMPLETED: (
                    "Your vehicle is ready. Thank you for choosing Motora."
                ),
                MaintenanceStatus.CANCELED: (
                    "Your maintenance request has been canceled."
                ),
            }

            status_message = status_messages.get(status)

            if status_message is None:
                return

            notification = EmailNotification(
                user_id=customer.id,
                maintenance_request_id=request.id,
                title="Maintenance Request Status Updated",
                subject="Motora — Maintenance Request Update",
                message=(
                    f"Your maintenance request for {car.make} {car.model} "
                    f"has been updated.\n\n"
                    f"Request ID: {request.id}\n"
                    f"New Status: {status.value}\n\n"
                    f"{status_message}"
                ),
                status=EmailStatus.PENDING,
            )

            notification = self.email_notification_repository.create(
                notification
            )

            try:
                self.email_service.send_maintenance_status_changed_email(
                    recipient=str(customer.email),
                    customer_name=(
                        f"{customer.first_name} {customer.last_name}"
                    ),
                    request_id=str(request.id),
                    vehicle_name=f"{car.make} {car.model}",
                    status=status.value,
                    status_message=status_message,
                )
            except Exception as error:
                print("STATUS EMAIL ERROR:", error)
                notification.status = EmailStatus.FAILED
                self.email_notification_repository.update(notification)
                return

            notification.status = EmailStatus.SENT
            notification.sent_at = datetime.now(timezone.utc)
            self.email_notification_repository.update(notification)

        except Exception as error:
            print("STATUS EMAIL ERROR:", error)


    def create_request(self, request: MaintenanceRequest) -> MaintenanceRequest:
        car = self.car_repository.find_by_id(request.car_id)

        if car is None:
            raise AppException("Car not found", status_code=404)

        return self.maintenance_request_repository.create(request)


    def get_request_by_id(self, request_id: UUID) -> MaintenanceRequest | None:
        request = self.maintenance_request_repository.find_by_id(request_id)
        if request is None:
            raise AppException("Maintenance request not found", status_code=404)
        return request


    def update_status(self, request_id: UUID, status: MaintenanceStatus):
        request = self.maintenance_request_repository.find_by_id(request_id)

        if request is None:
            raise AppException("Maintenance request not found", status_code=404)

        allowed_transitions = {
            MaintenanceStatus.PENDING: [MaintenanceStatus.ACCEPTED],
            MaintenanceStatus.ACCEPTED: [MaintenanceStatus.INSPECTING],
            MaintenanceStatus.INSPECTING: [
                MaintenanceStatus.AWAITING_APPROVAL,
                MaintenanceStatus.IN_PROGRESS,
            ],
            MaintenanceStatus.AWAITING_APPROVAL: [MaintenanceStatus.IN_PROGRESS],
            MaintenanceStatus.IN_PROGRESS: [MaintenanceStatus.COMPLETED],
        }

        if status not in allowed_transitions.get(request.status, []):
            raise AppException("Invalid maintenance status transition")

        if status in (MaintenanceStatus.IN_PROGRESS, MaintenanceStatus.COMPLETED):
            self._assert_no_pending_approvals(request_id)

        completed_at = None

        if status == MaintenanceStatus.COMPLETED:
            completed_at = datetime.now(timezone.utc).date()

        updated_request = self.maintenance_request_repository.update_status_if_current(
            request_id=request_id,
            current_status=request.status,
            new_status=status,
            completed_at=completed_at,
        )

        if updated_request is None:
            raise AppException(
                "Maintenance request has already changed. Please refresh and try again.",
                status_code=409,
            )

        self._notify_status(request_id, status)
        return updated_request


    def _assert_no_pending_approvals(self, request_id: UUID) -> None:
        """Work must not start, or be signed off, while the customer has
        not yet answered an additional service."""
        services = self.maintenance_service_repository.find_by_request_id(request_id)

        pending = [
            service
            for service in services
            if service.is_additional and service.approval == ApprovalStatus.PENDING
        ]

        if pending:
            raise AppException(
                f"Customer approval is still pending for {len(pending)} "
                "additional service(s)"
            )

    def cancel_request(self, request_id: UUID):
        request = self.maintenance_request_repository.find_by_id(request_id)

        if request is None:
            raise AppException("Maintenance request not found", status_code=404)

        if request.status == MaintenanceStatus.COMPLETED:
            raise AppException("Completed maintenance request cannot be canceled")

        if request.status == MaintenanceStatus.CANCELED:
            raise AppException("Maintenance request is already canceled")

        request.status = MaintenanceStatus.CANCELED

        updated = self.maintenance_request_repository.update(request)
        self._notify_status(request_id, MaintenanceStatus.CANCELED)
        return updated


    def calculate_total_cost(self, request_id: UUID) -> Decimal:
        services = self.maintenance_service_repository.find_by_request_id(
            request_id
        )

        total = Decimal("0.00")

        for service in services:
            if not service.is_additional:
                total += service.cost

            elif service.approval == ApprovalStatus.APPROVED:
                total += service.cost

        return total


    def calculate_balance(self, request_id: UUID) -> Decimal:
        total_cost = self.calculate_total_cost(request_id)

        payments = self.payment_repository.find_by_request_id(request_id)

        total_paid = Decimal("0.00")

        for payment in payments:
            total_paid += payment.amount

        return total_cost - total_paid


    def update_next_service_date(self, request_id: UUID, date: date):
        request = self.maintenance_request_repository.find_by_id(request_id)

        if request is None:
            raise AppException("Maintenance request not found", status_code=404)

        request.next_service_date = date

        return self.maintenance_request_repository.update(request)



