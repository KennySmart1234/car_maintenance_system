from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.enums.payment_method import PaymentMethod


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    maintenance_request_id: UUID = Field(
        foreign_key="maintenance_requests.id"
    )

    maintenance_service_id: UUID | None = Field(
        default=None,
        foreign_key="maintenance_services.id"
    )

    amount: Decimal
    payment_date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    method: PaymentMethod
    reference: str = Field(unique=True)