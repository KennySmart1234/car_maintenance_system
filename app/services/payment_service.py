from app.enums.notification_category import NotificationCategory
from app.services.notification_service import NotificationService

from decimal import Decimal
from uuid import uuid4

from sqlmodel import Session

from app.enums.approval_status import ApprovalStatus
from app.enums.maintenance_status import MaintenanceStatus
from app.exceptions.app_exception import AppException
from app.models.payment import Payment
from app.repositories.maintenance_request_repository import (
    MaintenanceRequestRepository,
)
from app.repositories.maintenance_service_repository import (
    MaintenanceServiceRepository,
)
from app.repositories.payment_repository import PaymentRepository


class PaymentService:

    def __init__(self, session: Session):
        self.payment_repository = PaymentRepository(session)
        self.notification_service = NotificationService(session)
        self.maintenance_request_repository = (
            MaintenanceRequestRepository(session)
        )
        self.maintenance_service_repository = (
            MaintenanceServiceRepository(session)
        )

    def create_payment(self, payment: Payment) -> Payment:
        if payment.amount <= Decimal("0"):
            raise AppException(
                "Payment amount must be greater than zero", status_code=400
            )


        if not payment.reference:
            payment.reference = f"PAY-{uuid4().hex.upper()}"


        existing_payment = self.payment_repository.find_by_reference(
            payment.reference
        )

        if existing_payment is not None:
            raise AppException("Payment reference already exists")


        request = self.maintenance_request_repository.find_by_id(
            payment.maintenance_request_id
        )

        if request is None:
            raise AppException("Maintenance request not found", status_code=404)

        if request.status == MaintenanceStatus.CANCELED:
            raise AppException(
                "Payment cannot be made for a cancelled request"
            )


        if payment.maintenance_service_id is None:
            raise AppException("Maintenance service ID is required", status_code=400)

        service = self.maintenance_service_repository.find_by_id_for_update(
            payment.maintenance_service_id
        )

        if service is None:
            raise AppException("Maintenance service not found", status_code=404)

        if service.maintenance_request_id != request.id:
            raise AppException(
                "Maintenance service does not belong to this request", status_code=400
            )

        if (
                service.is_additional
                and service.approval != ApprovalStatus.APPROVED
        ):
            raise AppException(
                "Additional service must be approved before payment"
            )

        previous_payments = (
            self.payment_repository.find_by_service_id(service.id)
        )

        total_paid = sum(
            (item.amount for item in previous_payments),
            Decimal("0.00"),
        )

        if total_paid + payment.amount > service.cost:
            raise AppException(
                "Payment exceeds the outstanding service balance", status_code=400
            )

        created = self.payment_repository.create(payment)

        notifier = getattr(self, "notification_service", None)
        if notifier is not None:
            notifier.notify_request_customer(
                request.id,
                NotificationCategory.PAYMENTS,
                "Payment Received",
                f"We received your payment of {created.amount} (ref {created.reference}).",
            )

        return created

