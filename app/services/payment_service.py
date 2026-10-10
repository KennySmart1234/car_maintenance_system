
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
        self.maintenance_request_repository = (
            MaintenanceRequestRepository(session)
        )
        self.maintenance_service_repository = (
            MaintenanceServiceRepository(session)
        )

    def create_payment(self, payment: Payment) -> Payment:
        if payment.amount <= Decimal("0"):
            raise AppException(
                "Payment amount must be greater than zero"
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
            raise AppException("Maintenance request not found")

        if request.status == MaintenanceStatus.CANCELED:
            raise AppException(
                "Payment cannot be made for a cancelled request"
            )


        if payment.maintenance_service_id is None:
            raise AppException("Maintenance service ID is required")

        service = self.maintenance_service_repository.find_by_id(
            payment.maintenance_service_id
        )

        if service is None:
            raise AppException("Maintenance service not found")

        if service.maintenance_request_id != request.id:
            raise AppException(
                "Maintenance service does not belong to this request"
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
                "Payment exceeds the outstanding service balance"
            )

        return self.payment_repository.create(payment)

