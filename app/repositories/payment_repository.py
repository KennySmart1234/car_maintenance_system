from select import select
from uuid import UUID

from sqlmodel import Session

from app.models.payment import Payment


class PaymentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, payment: Payment) -> Payment:
        self.session.add(payment)
        self.session.commit()
        self.session.refresh(payment)
        return payment


    def find_by_id(self, payment_id: UUID) -> Payment | None:
        statement = select(Payment).where(Payment.id == payment_id)
        return self.session.exec(statement).first()


    def find_by_request_id(self, request_id: UUID) -> list[Payment] | None:
        statement = select(Payment).where(Payment.maintenance_request_id == request_id)
        return list(self.session.exec(statement).all())


    def find_by_reference(self, reference: str) -> Payment | None:
        statement = select(Payment).where(
            Payment.reference == reference
        )
        return self.session.exec(statement).first()