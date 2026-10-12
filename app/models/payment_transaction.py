from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.enums.payment_transaction_status import PaymentTransactionStatus


class PaymentTransaction(SQLModel, table=True):
    __tablename__ = "payment_transactions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    reference: str = Field(unique=True, index=True)
    user_id: UUID = Field(foreign_key="users.id")
    maintenance_request_id: UUID = Field(foreign_key="maintenance_requests.id")
    maintenance_service_id: UUID = Field(foreign_key="maintenance_services.id")
    amount: Decimal
    status: PaymentTransactionStatus = Field(
        default=PaymentTransactionStatus.PENDING
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    paid_at: datetime | None = None