from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID, uuid4

from sqlmodel import Session

from app.config.settings import settings
from app.enums.approval_status import ApprovalStatus
from app.enums.maintenance_status import MaintenanceStatus
from app.enums.payment_method import PaymentMethod
from app.enums.payment_transaction_status import PaymentTransactionStatus
from app.exceptions.app_exception import AppException
from app.models.payment import Payment
from app.models.payment_transaction import PaymentTransaction
from app.models.user import User
from app.repositories.maintenance_request_repository import (
    MaintenanceRequestRepository,
)
from app.repositories.maintenance_service_repository import (
    MaintenanceServiceRepository,
)
from app.repositories.payment_repository import PaymentRepository
from app.repositories.payment_transaction_repository import (
    PaymentTransactionRepository,
)
from app.services import paystack_service
from app.services.payment_service import PaymentService


def _method_from_channel(channel: str | None) -> PaymentMethod:
    if channel in ("bank_transfer", "bank"):
        return PaymentMethod.TRANSFER
    return PaymentMethod.CARD


class PaystackPaymentService:
    def __init__(self, session: Session):
        self.session = session
        self.transaction_repository = PaymentTransactionRepository(session)
        self.service_repository = MaintenanceServiceRepository(session)
        self.request_repository = MaintenanceRequestRepository(session)
        self.payment_repository = PaymentRepository(session)
        self.payment_service = PaymentService(session)

    def start_payment(
        self, user: User, service_id: UUID, amount: Decimal | None
    ) -> dict:
        service = self.service_repository.find_by_id(service_id)

        if service is None:
            raise AppException("Maintenance service not found", status_code=404)

        request = self.request_repository.find_by_id(
            service.maintenance_request_id
        )

        if request.status == MaintenanceStatus.CANCELED:
            raise AppException("Payment cannot be made for a cancelled request")

        if service.is_additional and service.approval != ApprovalStatus.APPROVED:
            raise AppException("Additional service must be approved before payment")

        paid = sum(
            (p.amount for p in self.payment_repository.find_by_service_id(service.id)),
            Decimal("0"),
        )
        outstanding = (service.cost - paid).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        if outstanding <= 0:
            raise AppException("This service is already fully paid")

        if amount is None:
            amount = outstanding

        if amount > outstanding:
            raise AppException(
                "Amount exceeds the outstanding balance", status_code=400
            )

        reference = f"PSK-{uuid4().hex.upper()}"

        transaction = self.transaction_repository.create(
            PaymentTransaction(
                reference=reference,
                user_id=user.id,
                maintenance_request_id=request.id,
                maintenance_service_id=service.id,
                amount=amount,
            )
        )

        try:
            data = paystack_service.initialize_transaction(
                email=user.email,
                amount_kobo=paystack_service.to_kobo(amount),
                reference=reference,
                callback_url=f"{settings.app_base_url}/payments/paystack/callback",
            )
        except AppException:
            transaction.status = PaymentTransactionStatus.FAILED
            self.transaction_repository.save(transaction)
            raise

        return {
            "authorization_url": data["authorization_url"],
            "reference": reference,
        }

    def confirm_transaction(self, reference: str) -> PaymentTransaction:
        """Safe to call many times (callback AND webhook both call it)."""
        transaction = self.transaction_repository.find_by_reference_for_update(
            reference
        )

        if transaction is None:
            raise AppException("Payment transaction not found", status_code=404)

        if transaction.status != PaymentTransactionStatus.PENDING:
            return transaction  # already handled

        data = paystack_service.verify_transaction(reference)

        if data.get("status") != "success":
            return transaction  # not paid (yet): stay PENDING

        now = datetime.now(timezone.utc)

        if data.get("currency") != "NGN" or data.get(
            "amount"
        ) != paystack_service.to_kobo(transaction.amount):
            print("PAYSTACK AMOUNT MISMATCH for", reference)
            transaction.status = PaymentTransactionStatus.NEEDS_REVIEW
            transaction.paid_at = now
            return self.transaction_repository.save(transaction)

        transaction.status = PaymentTransactionStatus.SUCCESS
        transaction.paid_at = now
        self.session.add(transaction)

        payment = Payment(
            maintenance_request_id=transaction.maintenance_request_id,
            maintenance_service_id=transaction.maintenance_service_id,
            amount=transaction.amount,
            method=_method_from_channel(data.get("channel")),
            reference=transaction.reference,
        )

        try:
            # Re-runs the balance check and row lock; commits both rows together.
            self.payment_service.create_payment(payment)
        except AppException as error:
            # Money arrived but cannot be recorded (e.g. already paid in cash).
            # Never lose it silently: flag for a human to refund or fix.
            print("PAYSTACK NEEDS REVIEW:", reference, error.message)
            transaction.status = PaymentTransactionStatus.NEEDS_REVIEW
            transaction.paid_at = now
            self.transaction_repository.save(transaction)

        self.session.refresh(transaction)
        return transaction

    def list_transactions(
        self, status: PaymentTransactionStatus
    ) -> list[PaymentTransaction]:
        return self.transaction_repository.find_by_status(status)

    def resolve_transaction(self, reference: str) -> PaymentTransaction:
        """Staff confirm they dealt with it (refunded in Paystack, or fixed)."""
        transaction = self.transaction_repository.find_by_reference_for_update(
            reference
        )

        if transaction is None:
            raise AppException("Payment transaction not found", status_code=404)

        if transaction.status != PaymentTransactionStatus.NEEDS_REVIEW:
            raise AppException("Only transactions needing review can be resolved")

        transaction.status = PaymentTransactionStatus.RESOLVED
        return self.transaction_repository.save(transaction)