from datetime import datetime
from uuid import UUID
from app.models.car import Car
from app.models.maintenance_request import MaintenanceRequest

from uuid import UUID

from decimal import Decimal

from sqlalchemy import func
from sqlmodel import Session, select

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


    def find_by_service_id(
            self, service_id: UUID
    ) -> list[Payment]:
        statement = select(Payment).where(
            Payment.maintenance_service_id == service_id
        )
        return list(self.session.exec(statement).all())

    def total_received(self) -> Decimal:
        statement = select(func.coalesce(func.sum(Payment.amount), 0))
        return Decimal(self.session.exec(statement).one())

    def find_for_customer(self, customer_id: UUID) -> list[Payment]:
        statement = (
            select(Payment)
            .join(MaintenanceRequest, MaintenanceRequest.id == Payment.maintenance_request_id)
            .join(Car, Car.id == MaintenanceRequest.car_id)
            .where(Car.customer_id == customer_id)
            .order_by(Payment.payment_date.desc())
        )
        return list(self.session.exec(statement).all())

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Payment]:
        statement = (
            select(Payment).order_by(Payment.payment_date.desc()).offset(offset).limit(limit)
        )
        return list(self.session.exec(statement).all())

    def find_since(self, since: datetime) -> list[Payment]:
        statement = select(Payment).where(Payment.payment_date >= since)
        return list(self.session.exec(statement).all())
