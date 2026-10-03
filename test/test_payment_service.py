from uuid import uuid4

import pytest
from decimal import Decimal
from unittest.mock import Mock

from app.enums.maintenance_status import MaintenanceStatus
from app.enums.payment_method import PaymentMethod
from app.exceptions.app_exception import AppException
from app.models.payment import Payment
from app.services.payment_service import PaymentService


def test_create_payment_rejects_zero_amount():
    payment = Payment(
        maintenance_request_id=Mock(),
        amount=Decimal("0.00"),
        method=Mock(),
        reference="PAY-001",
        summaries="Test payment",
    )

    payment_repository = Mock()
    payment_service = PaymentService.__new__(PaymentService)
    payment_service.payment_repository = payment_repository

    with pytest.raises(AppException, match="Payment amount must be greater than zero"):
        payment_service.create_payment(payment)

    payment_repository.create.assert_not_called()


def test_create_payment_rejects_duplicate_reference():
    payment = Payment(
        maintenance_request_id=Mock(),
        amount=Decimal("5000.00"),
        method=Mock(),
        reference="PAY-001",
        summaries="Test payment",
    )

    payment_repository = Mock()
    payment_repository.find_by_reference.return_value = Mock()

    payment_service = PaymentService.__new__(PaymentService)
    payment_service.payment_repository = payment_repository

    with pytest.raises(AppException, match="Payment reference already exists"):
        payment_service.create_payment(payment)

    payment_repository.create.assert_not_called()


def test_create_payment_rejects_missing_maintenance_request():
    payment = Payment(
        maintenance_request_id=Mock(),
        amount=Decimal("5000.00"),
        method=Mock(),
        reference="PAY-002",
        summaries="Test payment",
    )

    payment_repository = Mock()
    payment_repository.find_by_reference.return_value = None

    maintenance_request_repository = Mock()
    maintenance_request_repository.find_by_id.return_value = None

    payment_service = PaymentService.__new__(PaymentService)
    payment_service.payment_repository = payment_repository
    payment_service.maintenance_request_repository = maintenance_request_repository

    with pytest.raises(AppException, match="Maintenance request not found"):
        payment_service.create_payment(payment)

    payment_repository.create.assert_not_called()


def test_create_payment_rejects_cancelled_maintenance_request():
    payment = Payment(
        maintenance_request_id=Mock(),
        amount=Decimal("5000.00"),
        method=Mock(),
        reference="PAY-003",
        summaries="Test payment",
    )

    payment_repository = Mock()
    payment_repository.find_by_reference.return_value = None

    maintenance_request = Mock()
    maintenance_request.status = MaintenanceStatus.CANCELED

    maintenance_request_repository = Mock()
    maintenance_request_repository.find_by_id.return_value = maintenance_request

    payment_service = PaymentService.__new__(PaymentService)
    payment_service.payment_repository = payment_repository
    payment_service.maintenance_request_repository = maintenance_request_repository

    with pytest.raises(
        AppException,
        match="Payment cannot be made for a cancelled request",
    ):
        payment_service.create_payment(payment)

    payment_repository.create.assert_not_called()


def test_create_payment_creates_valid_payment():
    payment = Payment(
        maintenance_request_id=uuid4(),
        amount=Decimal("5000.00"),
        method=PaymentMethod.TRANSFER,
        reference="PAY-VALID-001",
    )

    payment_repository = Mock()
    payment_repository.find_by_reference.return_value = None

    maintenance_request = Mock()
    maintenance_request.status = MaintenanceStatus.PENDING

    maintenance_request_repository = Mock()
    maintenance_request_repository.find_by_id.return_value = (
        maintenance_request
    )

    created_payment = payment

    payment_repository.create.return_value = created_payment

    payment_service = PaymentService.__new__(PaymentService)
    payment_service.payment_repository = payment_repository
    payment_service.maintenance_request_repository = (
        maintenance_request_repository
    )

    result = payment_service.create_payment(payment)

    assert result == created_payment
    payment_repository.create.assert_called_once_with(payment)