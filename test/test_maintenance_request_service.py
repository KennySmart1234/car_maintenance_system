from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4
from datetime import datetime, timezone

import pytest

from app.enums.approval_status import ApprovalStatus
from app.enums.maintenance_status import MaintenanceStatus
from app.exceptions.app_exception import AppException
from app.models.car import Car
from app.models.maintenance_request import MaintenanceRequest
from app.models.maintenance_service import MaintenanceService
from app.repositories.car_repository import CarRepository
from app.repositories.maintenance_request_repository import MaintenanceRequestRepository
from app.repositories.maintenance_service_repository import MaintenanceServiceRepository
from app.services.maintenance_request_service import MaintenanceRequestService
from app.models.payment import Payment
from app.enums.payment_method import PaymentMethod
from app.repositories.payment_repository import PaymentRepository


@pytest.fixture
def maintenance_request_service_dependencies():
    session = Mock()
    car_repository = Mock(spec=CarRepository)
    maintenance_request_repository = Mock(spec=MaintenanceRequestRepository)

    service = MaintenanceRequestService(session)

    service.car_repository = car_repository
    service.maintenance_request_repository = maintenance_request_repository

    return (
        service,
        car_repository,
        maintenance_request_repository,
    )


def test_create_request_successfully(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    car_id = uuid4()

    car = Car(
        id=car_id,
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2020,
        color="Black",
        plate_number="ABC123",
        vin="1HGBH41JXMN109186",
    )

    request = MaintenanceRequest(
        car_id=car_id,
        description="Replace brake pads",
        request_date=Mock(),
    )

    car_repository.find_by_id.return_value = car
    maintenance_request_repository.create.return_value = request

    result = service.create_request(request)

    assert result == request
    car_repository.find_by_id.assert_called_once_with(car_id)
    maintenance_request_repository.create.assert_called_once_with(request)




def test_create_request_raises_error_when_car_not_found(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    car_id = uuid4()

    request = MaintenanceRequest(
        car_id=car_id,
        description="Replace brake pads",
        request_date=Mock(),
    )

    car_repository.find_by_id.return_value = None

    with pytest.raises(AppException, match="Car not found"):
        service.create_request(request)

    car_repository.find_by_id.assert_called_once_with(car_id)
    maintenance_request_repository.create.assert_not_called()


def test_get_request_by_id_returns_request(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    request = MaintenanceRequest(
        id=request_id,
        car_id=uuid4(),
        description="Replace brake pads",
        request_date=Mock(),
    )

    maintenance_request_repository.find_by_id.return_value = request

    result = service.get_request_by_id(request_id)

    assert result == request
    maintenance_request_repository.find_by_id.assert_called_once_with(request_id)



def test_get_request_by_id_raises_error_when_request_not_found(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    maintenance_request_repository.find_by_id.return_value = None

    with pytest.raises(
        AppException,
        match="Maintenance request not found",
    ):
        service.get_request_by_id(request_id)

    maintenance_request_repository.find_by_id.assert_called_once_with(request_id)


def test_update_status_successfully(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    request = MaintenanceRequest(
        id=request_id,
        car_id=uuid4(),
        description="Replace brake pads",
        request_date=Mock(),
        status=MaintenanceStatus.PENDING,
    )

    maintenance_request_repository.find_by_id.return_value = request
    maintenance_request_repository.update.return_value = request

    result = service.update_status(
        request_id,
        MaintenanceStatus.ACCEPTED,
    )

    assert result == request
    assert request.status == MaintenanceStatus.ACCEPTED

    maintenance_request_repository.find_by_id.assert_called_once_with(request_id)
    maintenance_request_repository.update.assert_called_once_with(request)


def test_update_status_raises_error_when_request_not_found(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    maintenance_request_repository.find_by_id.return_value = None

    with pytest.raises(
        AppException,
        match="Maintenance request not found",
    ):
        service.update_status(
            request_id,
            MaintenanceStatus.ACCEPTED,
        )

    maintenance_request_repository.find_by_id.assert_called_once_with(request_id)
    maintenance_request_repository.update.assert_not_called()




def test_cancel_request_successfully(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    request = MaintenanceRequest(
        id=request_id,
        car_id=uuid4(),
        description="Replace brake pads",
        request_date=Mock(),
        status=MaintenanceStatus.PENDING,
    )

    maintenance_request_repository.find_by_id.return_value = request
    maintenance_request_repository.update.return_value = request

    result = service.cancel_request(request_id)

    assert result == request
    assert request.status == MaintenanceStatus.CANCELED

    maintenance_request_repository.find_by_id.assert_called_once_with(request_id)
    maintenance_request_repository.update.assert_called_once_with(request)



def test_calculate_total_cost_returns_sum_of_services(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    services = [
        MaintenanceService(
            maintenance_request_id=request_id,
            name="Brake pad replacement",
            description="Replace worn brake pads",
            cost=Decimal("50000.00"),
            is_additional=False,
        ),
        MaintenanceService(
            maintenance_request_id=request_id,
            name="Oil change",
            description="Replace engine oil",
            cost=Decimal("20000.00"),
            is_additional=False,
        ),
    ]

    service.maintenance_service_repository = Mock(
        spec = MaintenanceServiceRepository,
    )

    service.maintenance_service_repository.find_by_request_id.return_value = services

    result = service.calculate_total_cost(request_id)

    assert result == Decimal("70000.00")
    service.maintenance_service_repository.find_by_request_id.assert_called_once_with(
        request_id
    )


def test_calculate_total_cost_excludes_pending_additional_service(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    services = [
        MaintenanceService(
            maintenance_request_id=request_id,
            name="Brake pad replacement",
            description="Replace worn brake pads",
            cost=Decimal("50000.00"),
            is_additional=False,
        ),
        MaintenanceService(
            maintenance_request_id=request_id,
            name="Oil change",
            description="Replace engine oil",
            cost=Decimal("20000.00"),
            is_additional=False,
        ),
        MaintenanceService(
            maintenance_request_id=request_id,
            name="Wheel alignment",
            description="Additional wheel alignment",
            cost=Decimal("15000.00"),
            is_additional=True,
            approval=ApprovalStatus.PENDING,
        ),
    ]

    service.maintenance_service_repository = Mock(
        spec=MaintenanceServiceRepository,
    )

    service.maintenance_service_repository.find_by_request_id.return_value = (
        services
    )

    result = service.calculate_total_cost(request_id)

    assert result == Decimal("70000.00")



def test_calculate_total_cost_includes_approved_additional_service(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    services = [
        MaintenanceService(
            maintenance_request_id=request_id,
            name="Brake pad replacement",
            description="Replace worn brake pads",
            cost=Decimal("50000.00"),
            is_additional=False,
        ),

        MaintenanceService(
            maintenance_request_id=request_id,
            name="Oil change",
            description="Replace engine oil",
            cost=Decimal("20000.00"),
            is_additional=False,
        ),

        MaintenanceService(
            maintenance_request_id=request_id,
            name="Wheel alignment",
            description="Additional wheel alignment",
            cost=Decimal("15000.00"),
            is_additional=True,
            approval=ApprovalStatus.APPROVED,
        ),
    ]

    service.maintenance_service_repository = Mock(
        spec=MaintenanceServiceRepository,
    )

    service.maintenance_service_repository.find_by_request_id.return_value = (
        services
    )

    result = service.calculate_total_cost(request_id)

    assert result == Decimal("85000.00")





def test_calculate_total_cost_excludes_rejected_additional_service(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    services = [
        MaintenanceService(
            maintenance_request_id=request_id,
            name="Brake pad replacement",
            description="Replace worn brake pads",
            cost=Decimal("50000.00"),
            is_additional=False,
        ),
        MaintenanceService(
            maintenance_request_id=request_id,
            name="Oil change",
            description="Replace engine oil",
            cost=Decimal("20000.00"),
            is_additional=False,
        ),
        MaintenanceService(
            maintenance_request_id=request_id,
            name="Wheel alignment",
            description="Additional wheel alignment",
            cost=Decimal("15000.00"),
            is_additional=True,
            approval=ApprovalStatus.REJECTED,
        ),
    ]

    service.maintenance_service_repository = Mock(
        spec=MaintenanceServiceRepository,
    )

    service.maintenance_service_repository.find_by_request_id.return_value = (
        services
    )

    result = service.calculate_total_cost(request_id)

    assert result == Decimal("70000.00")





def test_calculate_total_cost_returns_zero_when_no_services_exist(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    service.maintenance_service_repository = Mock(
        spec=MaintenanceServiceRepository,
    )

    service.maintenance_service_repository.find_by_request_id.return_value = []

    result = service.calculate_total_cost(request_id)

    assert result == Decimal("0.00")



def test_calculate_balance_with_multiple_payments(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    services = [
        MaintenanceService(
            maintenance_request_id=request_id,
            name="Brake pad replacement",
            description="Replace worn brake pads",
            cost=Decimal("50000.00"),
            is_additional=False,
        ),
        MaintenanceService(
            maintenance_request_id=request_id,
            name="Oil change",
            description="Replace engine oil",
            cost=Decimal("20000.00"),
            is_additional=False,
        ),
    ]

    payments = [
        Payment(
            maintenance_request_id=request_id,
            amount=Decimal("20000.00"),
            reference="PAY-001",
        ),
        Payment(
            maintenance_request_id=request_id,
            amount=Decimal("15000.00"),
            reference="PAY-002",
        ),
    ]

    service.maintenance_service_repository = Mock(
        spec=MaintenanceServiceRepository,
    )
    service.payment_repository = Mock(
        spec=PaymentRepository,
    )

    service.maintenance_service_repository.find_by_request_id.return_value = (
        services
    )
    service.payment_repository.find_by_request_id.return_value = payments

    result = service.calculate_balance(request_id)

    assert result == Decimal("35000.00")




def test_calculate_balance_with_multiple_payments(
    maintenance_request_service_dependencies
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    service_1 = MaintenanceService(
        maintenance_request_id=request_id,
        name="Brake pad replacement",
        description="Replace brake pads",
        cost=Decimal("50000.00"),
        is_additional=False,
    )

    service_2 = MaintenanceService(
        maintenance_request_id=request_id,
        name="Wheel alignment",
        description="Align wheels",
        cost=Decimal("15000.00"),
        is_additional=True,
        approval=ApprovalStatus.APPROVED,
    )

    payment_1 = Payment(
        maintenance_request_id=request_id,
        amount=Decimal("20000.00"),
        method=PaymentMethod.TRANSFER,
        reference="REF001",
        description="First payment",
    )

    payment_2 = Payment(
        maintenance_request_id=request_id,
        amount=Decimal("15000.00"),
        method=PaymentMethod.TRANSFER,
        reference="REF002",
        description="Second payment",
    )

    service.maintenance_service_repository = Mock(
        spec=MaintenanceServiceRepository,
    )

    service.payment_repository = Mock(
        spec=PaymentRepository,
    )

    service.maintenance_service_repository.find_by_request_id.return_value = (
        [service_1, service_2]
    )

    service.payment_repository.find_by_request_id.return_value = (
        [payment_1, payment_2]
    )

    balance = service.calculate_balance(request_id)

    assert balance == Decimal("30000.00")


def test_calculate_balance_returns_total_cost_when_no_payments(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    service_1 = MaintenanceService(
        maintenance_request_id=request_id,
        name="Brake pad replacement",
        description="Replace brake pads",
        cost=Decimal("50000.00"),
        is_additional=False,
    )

    service_2 = MaintenanceService(
        maintenance_request_id=request_id,
        name="Wheel alignment",
        description="Align wheels",
        cost=Decimal("15000.00"),
        is_additional=True,
        approval=ApprovalStatus.APPROVED,
    )

    service.maintenance_service_repository = Mock(
        spec=MaintenanceServiceRepository,
    )

    service.payment_repository = Mock(
        spec=PaymentRepository,
    )

    service.maintenance_service_repository.find_by_request_id.return_value = (
        [service_1, service_2]
    )

    service.payment_repository.find_by_request_id.return_value = []

    balance = service.calculate_balance(request_id)

    assert balance == Decimal("65000.00")



def test_calculate_balance_returns_zero_when_fully_paid(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    service_1 = MaintenanceService(
        maintenance_request_id=request_id,
        name="Brake pad replacement",
        description="Replace brake pads",
        cost=Decimal("50000.00"),
        is_additional=False,
    )

    service_2 = MaintenanceService(
        maintenance_request_id=request_id,
        name="Wheel alignment",
        description="Align wheels",
        cost=Decimal("15000.00"),
        is_additional=True,
        approval=ApprovalStatus.APPROVED,
    )

    payment = Payment(
        maintenance_request_id=request_id,
        amount=Decimal("65000.00"),
        method=PaymentMethod.TRANSFER,
        reference="REF003",
        description="Full payment",
    )

    service.maintenance_service_repository = Mock(
        spec=MaintenanceServiceRepository,
    )

    service.payment_repository = Mock(
        spec=PaymentRepository,
    )

    service.maintenance_service_repository.find_by_request_id.return_value = (
        [service_1, service_2]
    )

    service.payment_repository.find_by_request_id.return_value = (
        [payment]
    )

    balance = service.calculate_balance(request_id)

    assert balance == Decimal("0.00")


def test_calculate_balance_returns_negative_when_overpaid(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    maintenance_service = MaintenanceService(
        maintenance_request_id=request_id,
        name="Brake pad replacement",
        description="Replace brake pads",
        cost=Decimal("50000.00"),
        is_additional=False,
    )

    payment = Payment(
        maintenance_request_id=request_id,
        amount=Decimal("60000.00"),
        method=PaymentMethod.TRANSFER,
        reference="REF004",
        description="Overpayment",
    )

    service.maintenance_service_repository = Mock(
        spec=MaintenanceServiceRepository,
    )

    service.payment_repository = Mock(
        spec=PaymentRepository,
    )

    service.maintenance_service_repository.find_by_request_id.return_value = (
        [maintenance_service]
    )

    service.payment_repository.find_by_request_id.return_value = (
        [payment]
    )

    balance = service.calculate_balance(request_id)

    assert balance == Decimal("-10000.00")



def test_calculate_balance_returns_zero_when_no_services_and_no_payments(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    service.maintenance_service_repository = Mock(
        spec=MaintenanceServiceRepository,
    )

    service.payment_repository = Mock(
        spec=PaymentRepository,
    )

    service.maintenance_service_repository.find_by_request_id.return_value = []

    service.payment_repository.find_by_request_id.return_value = []

    balance = service.calculate_balance(request_id)

    assert balance == Decimal("0.00")


def test_update_status_raises_error_when_skipping_status(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    maintenance_request = MaintenanceRequest(
        id=request_id,
        car_id=uuid4(),
        description="Brake problem with the car",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.PENDING,
    )

    service.maintenance_request_repository = Mock(
        spec=MaintenanceRequestRepository,
    )

    service.maintenance_request_repository.find_by_id.return_value = (
        maintenance_request
    )

    with pytest.raises(AppException) as exc:
        service.update_status(
            request_id,
            MaintenanceStatus.COMPLETED,
        )

    assert str(exc.value) == "Invalid maintenance status transition"



def test_update_status_allows_valid_transition(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    maintenance_request = MaintenanceRequest(
        id=request_id,
        car_id=uuid4(),
        description="Brake problem with the car",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.PENDING,
    )

    service.maintenance_request_repository = Mock(
        spec=MaintenanceRequestRepository,
    )

    service.maintenance_request_repository.find_by_id.return_value = (
        maintenance_request
    )

    service.maintenance_request_repository.update.return_value = (
        maintenance_request
    )

    result = service.update_status(
        request_id,
        MaintenanceStatus.ACCEPTED,
    )

    assert result.status == MaintenanceStatus.ACCEPTED



def test_update_status_allows_accepted_to_inspecting(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    maintenance_request = MaintenanceRequest(
        id=request_id,
        car_id=uuid4(),
        description="Brake problem with the car",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.ACCEPTED,
    )

    service.maintenance_request_repository = Mock(
        spec=MaintenanceRequestRepository,
    )

    service.maintenance_request_repository.find_by_id.return_value = (
        maintenance_request
    )

    service.maintenance_request_repository.update.return_value = (
        maintenance_request
    )

    result = service.update_status(
        request_id,
        MaintenanceStatus.INSPECTING,
    )

    assert result.status == MaintenanceStatus.INSPECTING



def test_update_status_allows_inspecting_to_awaiting_approval(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    maintenance_request = MaintenanceRequest(
        id=request_id,
        car_id=uuid4(),
        description="Brake problem with the car",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.INSPECTING,
    )

    service.maintenance_request_repository = Mock(
        spec=MaintenanceRequestRepository,
    )

    service.maintenance_request_repository.find_by_id.return_value = (
        maintenance_request
    )

    service.maintenance_request_repository.update.return_value = (
        maintenance_request
    )

    result = service.update_status(
        request_id,
        MaintenanceStatus.AWAITING_APPROVAL,
    )

    assert result.status == MaintenanceStatus.AWAITING_APPROVAL


def test_update_status_allows_awaiting_approval_to_in_progress(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    maintenance_request = MaintenanceRequest(
        id=request_id,
        car_id=uuid4(),
        description="Brake problem with the car",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.AWAITING_APPROVAL,
    )

    service.maintenance_request_repository = Mock(
        spec=MaintenanceRequestRepository,
    )

    service.maintenance_request_repository.find_by_id.return_value = (
        maintenance_request
    )

    service.maintenance_request_repository.update.return_value = (
        maintenance_request
    )

    result = service.update_status(
        request_id,
        MaintenanceStatus.IN_PROGRESS,
    )

    assert result.status == MaintenanceStatus.IN_PROGRESS



def test_update_status_allows_in_progress_to_completed(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    maintenance_request = MaintenanceRequest(
        id=request_id,
        car_id=uuid4(),
        description="Brake problem with the car",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.IN_PROGRESS,
    )

    service.maintenance_request_repository = Mock(
        spec=MaintenanceRequestRepository,
    )

    service.maintenance_request_repository.find_by_id.return_value = (
        maintenance_request
    )

    service.maintenance_request_repository.update.return_value = (
        maintenance_request
    )

    result = service.update_status(
        request_id,
        MaintenanceStatus.COMPLETED,
    )

    assert result.status == MaintenanceStatus.COMPLETED



def test_cancel_request_raises_error_when_request_is_completed(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    maintenance_request = MaintenanceRequest(
        id=request_id,
        car_id=uuid4(),
        description="Brake problem with the car",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.COMPLETED,
    )

    service.maintenance_request_repository = Mock(
        spec=MaintenanceRequestRepository,
    )

    service.maintenance_request_repository.find_by_id.return_value = (
        maintenance_request
    )

    with pytest.raises(AppException) as exc:
        service.cancel_request(request_id)

    assert str(exc.value) == "Completed maintenance request cannot be canceled"



def test_cancel_request_raises_error_when_request_is_already_canceled(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request_id = uuid4()

    maintenance_request = MaintenanceRequest(
        id=request_id,
        car_id=uuid4(),
        description="Brake problem with the car",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.CANCELED,
    )

    service.maintenance_request_repository = Mock(
        spec=MaintenanceRequestRepository,
    )

    service.maintenance_request_repository.find_by_id.return_value = (
        maintenance_request
    )

    with pytest.raises(AppException) as exc:
        service.cancel_request(request_id)

    assert str(exc.value) == "Maintenance request is already canceled"



def test_update_status_allows_inspecting_to_in_progress_without_additional_service(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request = MaintenanceRequest(
        id=uuid4(),
        car_id=uuid4(),
        description="Brake pad replacement",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.INSPECTING,
    )

    maintenance_request_repository.find_by_id.return_value = request
    maintenance_request_repository.update.return_value = request

    result = service.update_status(
        request.id,
        MaintenanceStatus.IN_PROGRESS,
    )

    assert result.status == MaintenanceStatus.IN_PROGRESS




def test_update_status_rejects_same_status_transition(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request = MaintenanceRequest(
        id=uuid4(),
        car_id=uuid4(),
        description="Brake pad replacement",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.PENDING,
    )

    maintenance_request_repository.find_by_id.return_value = request

    with pytest.raises(AppException, match="Invalid maintenance status transition"):
        service.update_status(
            request.id,
            MaintenanceStatus.PENDING,
        )


def test_update_status_rejects_backward_transition(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request = MaintenanceRequest(
        id=uuid4(),
        car_id=uuid4(),
        description="Brake pad replacement",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.IN_PROGRESS,
    )

    maintenance_request_repository.find_by_id.return_value = request

    with pytest.raises(AppException, match="Invalid maintenance status transition"):
        service.update_status(
            request.id,
            MaintenanceStatus.INSPECTING,
        )


def test_update_status_rejects_transition_from_canceled_request(
    maintenance_request_service_dependencies,
):
    service, car_repository, maintenance_request_repository = (
        maintenance_request_service_dependencies
    )

    request = MaintenanceRequest(
        id=uuid4(),
        car_id=uuid4(),
        description="Brake pad replacement",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.CANCELED,
    )

    maintenance_request_repository.find_by_id.return_value = request

    with pytest.raises(AppException, match="Invalid maintenance status transition"):
        service.update_status(
            request.id,
            MaintenanceStatus.IN_PROGRESS,
        )


