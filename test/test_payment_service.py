import pytest
from pydantic import ValidationError

from app.enums.payment_method import PaymentMethod
from app.schemas.payment_schema import PaymentCreate


def test_payment_create_rejects_zero_amount():
    with pytest.raises(ValidationError):
        PaymentCreate(
            maintenance_request_id="550e8400-e29b-41d4-a716-446655440000",
            amount=0,
            method=PaymentMethod.TRANSFER,
            reference="PAY-001",
        )