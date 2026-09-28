from decimal import Decimal
from uuid import UUID

from pydantic import Field
from sqlmodel import SQLModel

from app.enums.payment_method import PaymentMethod


class PaymentCreate(SQLModel):
    maintenance_request_id: UUID
    amount: Decimal = Field(gt=0)
    method: PaymentMethod
    reference: str = Field(min_length=1)
    description: str = Field(..., min_length=5)