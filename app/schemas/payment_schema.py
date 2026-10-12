from decimal import Decimal
from uuid import UUID
from datetime import datetime
from app.enums.payment_transaction_status import PaymentTransactionStatus
from pydantic import Field
from sqlmodel import SQLModel

from app.enums.payment_method import PaymentMethod


class PaymentCreate(SQLModel):
    maintenance_request_id: UUID
    maintenance_service_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    method: PaymentMethod

class PaystackInitializeRequest(SQLModel):
    maintenance_service_id: UUID
    amount: Decimal | None = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )

class PaymentTransactionResponse(SQLModel):
    id: UUID
    reference: str
    user_id: UUID
    maintenance_request_id: UUID
    maintenance_service_id: UUID
    amount: Decimal
    status: PaymentTransactionStatus
    created_at: datetime
    paid_at: datetime | None = None