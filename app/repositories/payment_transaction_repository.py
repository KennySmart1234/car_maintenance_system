from sqlalchemy import func
from sqlmodel import Session, select

from app.models.payment_transaction import PaymentTransaction
from app.enums.payment_transaction_status import PaymentTransactionStatus

class PaymentTransactionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, transaction: PaymentTransaction) -> PaymentTransaction:
        return self.save(transaction)

    def save(self, transaction: PaymentTransaction) -> PaymentTransaction:
        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)
        return transaction

    def find_by_reference_for_update(
        self, reference: str
    ) -> PaymentTransaction | None:
        statement = (
            select(PaymentTransaction)
            .where(PaymentTransaction.reference == reference)
            .with_for_update()
        )
        return self.session.exec(statement).first()

    def find_by_status(
        self, status: PaymentTransactionStatus, limit: int | None = None
    ) -> list[PaymentTransaction]:
        statement = (
            select(PaymentTransaction)
            .where(PaymentTransaction.status == status)
            .order_by(PaymentTransaction.created_at.desc())
        )

        if limit is not None:
            statement = statement.limit(limit)

        return list(self.session.exec(statement).all())

    def count_by_status(self, status: PaymentTransactionStatus) -> int:
        statement = select(func.count(PaymentTransaction.id)).where(
            PaymentTransaction.status == status
        )
        return self.session.exec(statement).one()