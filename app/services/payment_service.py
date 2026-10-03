from decimal import Decimal

from sqlmodel import Session

from app.enums.maintenance_status import MaintenanceStatus
from app.exceptions.app_exception import AppException
from app.models.payment import Payment
from app.repositories.maintenance_request_repository import MaintenanceRequestRepository
from app.repositories.payment_repository import PaymentRepository


class PaymentService:

    def __init__(self, session: Session):
        self.payment_repository = PaymentRepository(session)
        self.maintenance_request_repository = MaintenanceRequestRepository(session)

    def create_payment(self, payment: Payment) -> Payment:
        if payment.amount <= Decimal("0"):
            raise AppException("Payment amount must be greater than zero")

        existing_payment = self.payment_repository.find_by_reference(
            payment.reference
        )

        if existing_payment is not None:
            raise AppException("Payment reference already exists")

        maintenance_request = self.maintenance_request_repository.find_by_id(
            payment.maintenance_request_id
        )

        if maintenance_request is None:
            raise AppException("Maintenance request not found")

        if maintenance_request.status == MaintenanceStatus.CANCELED:
            raise AppException("Payment cannot be made for a cancelled request")

        return self.payment_repository.create(payment)