from datetime import datetime, timezone
from decimal import Decimal

import pytest

from unittest.mock import Mock
from uuid import uuid4


from app.repositories.maintenance_service_repository import MaintenanceServiceRepository
from app.enums.approval_status import ApprovalStatus
from app.enums.maintenance_status import MaintenanceStatus
from app.enums.payment_method import PaymentMethod
from app.exceptions.app_exception import AppException
from app.models.car import Car
from app.models.maintenance_request import MaintenanceRequest
from app.models.maintenance_service import MaintenanceService
from app.models.payment import Payment
from app.schemas.maintenance_request_schema import MaintenanceRequestCreate
from app.services.customer_service import CustomerService


@pytest.fixture
def customer_service_dependencies():
    session = Mock()
    car_repository = Mock()
    maintenance_request_repository = Mock()

    customer_service = CustomerService(session)
    customer_service.car_repository = car_repository
    customer_service.maintenance_request_repository = (
        maintenance_request_repository
    )

    return (
        customer_service,
        car_repository,
        maintenance_request_repository,
    )


def test_add_car_returns_created_car():
    session = Mock()
    car_repository = Mock()

    customer_service = CustomerService(session)
    customer_service.car_repository = car_repository

    car = Car(
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None
    car_repository.create.return_value = car

    result = customer_service.add_car(car)

    assert result == car

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.find_by_vin.assert_called_once_with(
        "1HGCM82633A123456"
    )

    car_repository.create.assert_called_once_with(car)


def test_add_car_with_complete_car_data():
    session = Mock()
    car_repository = Mock()

    customer_service = CustomerService(session)
    customer_service.car_repository = car_repository

    car = Car(
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None
    car_repository.create.return_value = car

    result = customer_service.add_car(car)

    assert result == car

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.find_by_vin.assert_called_once_with(
        "1HGCM82633A123456"
    )

    car_repository.create.assert_called_once_with(car)


def test_add_car_returns_created_car():
    session = Mock()
    car_repository = Mock()

    customer_service = CustomerService(session)
    customer_service.car_repository = car_repository

    car = Mock()

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None
    car_repository.create.return_value = car

    result = customer_service.add_car(car)

    assert result == car

    car_repository.find_by_plate_number.assert_called_once_with(
        car.plate_number
    )

    car_repository.find_by_vin.assert_called_once_with(
        car.vin
    )

    car_repository.create.assert_called_once_with(car)


def test_add_car_rejects_duplicate_plate_number_with_complete_car():
    session = Mock()
    car_repository = Mock()

    customer_service = CustomerService(session)
    customer_service.car_repository = car_repository

    car = Car(
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    existing_car = Car(
        customer_id=uuid4(),
        make="Honda",
        model="Accord",
        year=2021,
        color="White",
        plate_number="ABC-123",
        vin="2HGCM82633A654321"
    )

    car_repository.find_by_plate_number.return_value = existing_car

    with pytest.raises(AppException, match="Plate number already exists"):
        customer_service.add_car(car)

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.find_by_vin.assert_not_called()
    car_repository.create.assert_not_called()


def test_add_car_when_plate_number_is_available():
    session = Mock()
    car_repository = Mock()

    customer_service = CustomerService(session)
    customer_service.car_repository = car_repository

    car = Mock()
    car.plate_number = "ABC-123"
    car.vin = "1HGCM82633A123456"

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None
    car_repository.create.return_value = car

    result = customer_service.add_car(car)

    assert result == car

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.find_by_vin.assert_called_once_with(
        "1HGCM82633A123456"
    )

    car_repository.create.assert_called_once_with(car)


def test_add_car_rejects_duplicate_plate_number():
    session = Mock()
    car_repository = Mock()

    customer_service = CustomerService(session)
    customer_service.car_repository = car_repository

    existing_car = Mock()
    car_repository.find_by_plate_number.return_value = existing_car

    car = Mock()
    car.plate_number = "ABC-123"

    with pytest.raises(AppException, match="Plate number already exists"):
        customer_service.add_car(car)

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.create.assert_not_called()


def test_add_car_rejects_duplicate_vin():
    session = Mock()
    car_repository = Mock()

    customer_service = CustomerService(session)
    customer_service.car_repository = car_repository

    existing_car = Mock()
    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = existing_car

    car = Mock()
    car.plate_number = "ABC-123"
    car.vin = "1HGCM82633A123456"

    with pytest.raises(AppException, match="VIN already exists"):
        customer_service.add_car(car)

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.find_by_vin.assert_called_once_with(
        "1HGCM82633A123456"
    )

    car_repository.create.assert_not_called()


def test_add_car_rejects_duplicate_vin_with_complete_car(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    car = Car(
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    existing_car = Car(
        customer_id=uuid4(),
        make="Honda",
        model="Accord",
        year=2021,
        color="White",
        plate_number="XYZ-789",
        vin="1HGCM82633A123456"
    )

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = existing_car

    with pytest.raises(AppException, match="VIN already exists"):
        customer_service.add_car(car)

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.find_by_vin.assert_called_once_with(
        "1HGCM82633A123456"
    )

    car_repository.create.assert_not_called()


def test_add_car_checks_vin_after_plate_is_available(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    car = Mock()
    car.plate_number = "ABC-123"
    car.vin = "1HGCM82633A123456"

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None
    car_repository.create.return_value = car

    result = customer_service.add_car(car)

    assert result == car

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.find_by_vin.assert_called_once_with(
        "1HGCM82633A123456"
    )

    car_repository.create.assert_called_once_with(car)


def test_add_car_accepts_unique_plate_and_vin(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    car = Car(
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None
    car_repository.create.return_value = car

    result = customer_service.add_car(car)

    assert result == car
    assert result.make == "Toyota"
    assert result.model == "Camry"
    assert result.year == 2022
    assert result.color == "Black"
    assert result.plate_number == "ABC-123"
    assert result.vin == "1HGCM82633A123456"

    car_repository.create.assert_called_once_with(car)


def test_add_car_rejects_duplicate_plate_and_vin(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    car = Car(
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    existing_car = Car(
        customer_id=uuid4(),
        make="Honda",
        model="Accord",
        year=2021,
        color="White",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    car_repository.find_by_plate_number.return_value = existing_car
    car_repository.find_by_vin.return_value = existing_car

    with pytest.raises(
        AppException,
        match="Plate number already exists"
    ):
        customer_service.add_car(car)

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.find_by_vin.assert_not_called()
    car_repository.create.assert_not_called()


def test_add_car_rejects_same_vin_with_different_plate(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    car = Car(
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="NEW-123",
        vin="1HGCM82633A123456"
    )

    existing_car = Car(
        customer_id=uuid4(),
        make="Honda",
        model="Accord",
        year=2021,
        color="White",
        plate_number="OLD-456",
        vin="1HGCM82633A123456"
    )

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = existing_car

    with pytest.raises(AppException, match="VIN already exists"):
        customer_service.add_car(car)

    car_repository.create.assert_not_called()


def test_add_car_returns_car_from_repository(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    car = Car(
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    saved_car = Car(
        customer_id=car.customer_id,
        make=car.make,
        model=car.model,
        year=car.year,
        color=car.color,
        plate_number=car.plate_number,
        vin=car.vin
    )

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None
    car_repository.create.return_value = saved_car

    result = customer_service.add_car(car)

    assert result is saved_car
    assert result is not car


def test_add_car_propagates_repository_create_error(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    car = Car(
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None
    car_repository.create.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        customer_service.add_car(car)


def test_add_car_allows_different_customers_to_register_cars(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    customer_one = uuid4()
    customer_two = uuid4()

    car_one = Car(
        customer_id=customer_one,
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    car_two = Car(
        customer_id=customer_two,
        make="Honda",
        model="Accord",
        year=2023,
        color="White",
        plate_number="XYZ-789",
        vin="2HGCM82633B654321"
    )

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None
    car_repository.create.side_effect = [car_one, car_two]

    result_one = customer_service.add_car(car_one)
    result_two = customer_service.add_car(car_two)

    assert result_one == car_one
    assert result_two == car_two

    assert car_repository.create.call_count == 2



def test_get_cars_returns_empty_list_when_customer_has_no_cars(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    customer_id = uuid4()

    car_repository.find_by_customer_id.return_value = []

    result = customer_service.get_cars(customer_id)

    assert result == []

    car_repository.find_by_customer_id.assert_called_once_with(
        customer_id
    )


def test_get_cars_returns_single_car(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    customer_id = uuid4()

    car = Car(
        customer_id=customer_id,
        make="Toyota",
        model="Corolla",
        year=2021,
        color="Blue",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    car_repository.find_by_customer_id.return_value = [car]

    result = customer_service.get_cars(customer_id)

    assert result == [car]

    car_repository.find_by_customer_id.assert_called_once_with(
        customer_id
    )


def test_get_cars_returns_only_repository_results(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    customer_id = uuid4()
    other_customer_id = uuid4()

    customer_car = Car(
        customer_id=customer_id,
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    other_car = Car(
        customer_id=other_customer_id,
        make="Honda",
        model="Accord",
        year=2023,
        color="White",
        plate_number="XYZ-789",
        vin="2HGCM82633B654321"
    )

    car_repository.find_by_customer_id.return_value = [customer_car]

    result = customer_service.get_cars(customer_id)

    assert result == [customer_car]
    assert other_car not in result

    car_repository.find_by_customer_id.assert_called_once_with(
        customer_id
    )


def test_get_cars_propagates_repository_error(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    customer_id = uuid4()

    car_repository.find_by_customer_id.side_effect = Exception(
        "Database error"
    )

    with pytest.raises(Exception, match="Database error"):
        customer_service.get_cars(customer_id)

    car_repository.find_by_customer_id.assert_called_once_with(
        customer_id
    )


def test_get_cars_returns_all_customer_cars(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    customer_id = uuid4()
    car_one = Car(
        customer_id=customer_id,
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    car_two = Car(
        customer_id=customer_id,
        make="Honda",
        model="Accord",
        year=2023,
        color="White",
        plate_number="XYZ-789",
        vin="2HGCM82633B654321"
    )

    car_repository.find_by_customer_id.return_value = [
        car_one,
        car_two
    ]

    result = customer_service.get_cars(customer_id)

    assert result == [car_one, car_two]

    car_repository.find_by_customer_id.assert_called_once_with(
        customer_id
    )



def test_submit_request_returns_created_request(
        customer_service_dependencies ):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies


    car_id = uuid4()

    request_data = MaintenanceRequestCreate(
        car_id=car_id,
        description="Oil change and brake inspection",
        request_date=datetime.now(timezone.utc),
    )

    car_repository.find_by_id.return_value = Mock()

    created_request = Mock()
    maintenance_request_repository.create.return_value = created_request

    result = customer_service.submit_request(request_data)

    assert result == created_request



def test_submit_request_raises_error_when_car_not_found(
        customer_service_dependencies ):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies


    car_id = uuid4()

    request_data = MaintenanceRequestCreate(
        car_id=car_id,
        description="Oil change and brake inspection",
        request_date=datetime.now(timezone.utc),
    )

    car_repository.find_by_id.return_value = None

    with pytest.raises(AppException, match="Car not found"):
        customer_service.submit_request(request_data)

    car_repository.find_by_id.assert_called_once_with(car_id)


def test_submit_request_does_not_create_request_when_car_not_found(
        customer_service_dependencies ):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies


    car_id = uuid4()

    request_data = MaintenanceRequestCreate(
        car_id=car_id,
        description="Oil change and brake inspection",
        request_date=datetime.now(timezone.utc),
    )

    car_repository.find_by_id.return_value = None

    with pytest.raises(AppException, match="Car not found"):
        customer_service.submit_request(request_data)

    maintenance_request_repository.create.assert_not_called()



def test_submit_request_creates_request_with_correct_data(
        customer_service_dependencies ):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies


    car_id = uuid4()
    request_date = datetime.now(timezone.utc)

    request_data = MaintenanceRequestCreate(
        car_id=car_id,
        description="Oil change and brake inspection",
        request_date=request_date,
    )

    car_repository.find_by_id.return_value = Mock()

    created_request = Mock()
    maintenance_request_repository.create.return_value = created_request

    customer_service.submit_request(request_data)

    created_request_arg = (
        maintenance_request_repository.create.call_args[0][0]
    )

    assert created_request_arg.car_id == car_id
    assert created_request_arg.description == "Oil change and brake inspection"
    assert created_request_arg.request_date == request_date



def test_submit_request_creates_request_with_pending_status(
        customer_service_dependencies ):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies


    car_id = uuid4()

    request_data = MaintenanceRequestCreate(
        car_id=car_id,
        description="Oil change and brake inspection",
        request_date=datetime.now(timezone.utc),
    )

    car_repository.find_by_id.return_value = Mock()
    maintenance_request_repository.create.return_value = Mock()

    customer_service.submit_request(request_data)

    created_request = (
        maintenance_request_repository.create.call_args[0][0]
    )

    assert created_request.status == MaintenanceStatus.PENDING



def test_submit_request_preserves_description(
        customer_service_dependencies ):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies


    car_id = uuid4()
    description = "Engine oil change and complete brake inspection"

    request_data = MaintenanceRequestCreate(
        car_id=car_id,
        description=description,
        request_date=datetime.now(timezone.utc),
    )

    car_repository.find_by_id.return_value = Mock()
    maintenance_request_repository.create.return_value = Mock()

    customer_service.submit_request(request_data)

    created_request = (
        maintenance_request_repository.create.call_args[0][0]
    )

    assert created_request.description == description

def test_submit_request_preserves_request_date(
        customer_service_dependencies ):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    car_id = uuid4()
    request_date = datetime(2026, 10, 5, 10, 30, tzinfo=timezone.utc)

    request_data = MaintenanceRequestCreate(
        car_id=car_id,
        description="Oil change and brake inspection",
        request_date=request_date,
    )

    car_repository.find_by_id.return_value = Mock()
    maintenance_request_repository.create.return_value = Mock()

    customer_service.submit_request(request_data)

    created_request = (
        maintenance_request_repository.create.call_args[0][0]
    )

    assert created_request.request_date == request_date


def test_submit_request_propagates_repository_create_error(
        customer_service_dependencies):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    car_id = uuid4()

    request_data = MaintenanceRequestCreate(
        car_id=car_id,
        description="Oil change and brake inspection",
        request_date=datetime.now(timezone.utc),
    )

    car_repository.find_by_id.return_value = Mock()

    error = Exception("Database error")
    maintenance_request_repository.create.side_effect = error

    with pytest.raises(Exception, match="Database error"):
        customer_service.submit_request(request_data)

    maintenance_request_repository.create.assert_called_once()



def test_approve_work_approves_additional_service(
    customer_service_dependencies,
):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    service = MaintenanceService(
        maintenance_request_id=uuid4(),
        name="Brake Pad Replacement",
        description="Replace worn brake pads",
        cost = 50000,
        is_additional=True,
    )

    service_repository = Mock()
    service_repository.find_by_id.return_value = service
    service_repository.update.return_value = service
    customer_service.maintenance_service_repository = service_repository

    result = customer_service.approve_work(service.id)

    assert result.approval == ApprovalStatus.APPROVED
    service_repository.update.assert_called_once_with(service)


def test_approve_work_raises_error_when_service_not_found(
    customer_service_dependencies,
):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    service_repository = Mock()
    service_repository.find_by_id.return_value = None
    customer_service.maintenance_service_repository = service_repository

    with pytest.raises(AppException, match="Maintenance service not found"):
        customer_service.approve_work(uuid4())



def test_approve_work_rejects_non_additional_service(
    customer_service_dependencies,
):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    service = MaintenanceService(
        maintenance_request_id=uuid4(),
        name="Oil Change",
        description="Regular oil change",
        cost=30000,
        is_additional=False,
    )

    service_repository = Mock()
    service_repository.find_by_id.return_value = service
    customer_service.maintenance_service_repository = service_repository

    with pytest.raises(
        AppException,
        match="Only additional services require approval",
    ):
        customer_service.approve_work(service.id)

    service_repository.update.assert_not_called()


def test_approve_work_rejects_already_approved_service(
    customer_service_dependencies,
):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    service = MaintenanceService(
        maintenance_request_id=uuid4(),
        name="Brake Pad Replacement",
        description="Replace worn brake pads",
        cost=50000,
        is_additional=True,
        approval=ApprovalStatus.APPROVED,
    )

    service_repository = Mock()
    service_repository.find_by_id.return_value = service
    customer_service.maintenance_service_repository = service_repository

    with pytest.raises(
        AppException,
        match="Maintenance service is already approved",
    ):
        customer_service.approve_work(service.id)

    service_repository.update.assert_not_called()

def test_approve_work_rejects_rejected_service(
    customer_service_dependencies,
):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    service = MaintenanceService(
        maintenance_request_id=uuid4(),
        name="Brake Pad Replacement",
        description="Replace worn brake pads",
        cost=50000,
        is_additional=True,
        approval=ApprovalStatus.REJECTED,
    )

    service_repository = Mock()
    service_repository.find_by_id.return_value = service
    customer_service.maintenance_service_repository = service_repository

    with pytest.raises(
        AppException,
        match="Rejected maintenance service cannot be approved",
    ):
        customer_service.approve_work(service.id)

    service_repository.update.assert_not_called()



def test_view_history_returns_car_maintenance_history(
    customer_service_dependencies,
):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    car_id = uuid4()

    maintenance_request = MaintenanceRequest(
        car_id=car_id,
        description="Oil change",
        request_date=datetime.now(timezone.utc),
    )

    maintenance_request_repository.find_by_car_id.return_value = [
        maintenance_request
    ]

    result = customer_service.view_history(car_id)

    assert result == [maintenance_request]
    maintenance_request_repository.find_by_car_id.assert_called_once_with(
        car_id
    )



def test_view_history_returns_empty_list_when_car_has_no_history(
    customer_service_dependencies,
):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    car_id = uuid4()

    maintenance_request_repository.find_by_car_id.return_value = []

    result = customer_service.view_history(car_id)

    assert result == []
    maintenance_request_repository.find_by_car_id.assert_called_once_with(
        car_id
    )



def test_view_history_returns_none_when_repository_returns_none(
    customer_service_dependencies,
):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    car_id = uuid4()

    maintenance_request_repository.find_by_car_id.return_value = None

    result = customer_service.view_history(car_id)

    assert result is None
    maintenance_request_repository.find_by_car_id.assert_called_once_with(
        car_id
    )



def test_make_payment_creates_payment(
    customer_service_dependencies,
):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    payment_repository = Mock()
    customer_service.payment_repository = payment_repository
    payment_repository.find_by_reference.return_value = None

    payment = Payment(
        request_id=uuid4(),
        amount=50000,
        method=PaymentMethod.TRANSFER,
        reference="PAY-12345",
    )

    payment_repository.create.return_value = payment

    result = customer_service.make_payment(payment)

    assert result == payment
    payment_repository.create.assert_called_once_with(payment)


def test_make_payment_returns_none_when_repository_returns_none(
    customer_service_dependencies,
):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    payment_repository = Mock()
    customer_service.payment_repository = payment_repository
    payment_repository.find_by_reference.return_value = None

    payment = Payment(
        request_id=uuid4(),
        amount=50000,
        method=PaymentMethod.TRANSFER,
        reference="PAY-12345",
    )

    payment_repository.create.return_value = None

    result = customer_service.make_payment(payment)

    assert result is None
    payment_repository.create.assert_called_once_with(payment)


def test_make_payment_raises_error_when_request_not_found(
    customer_service_dependencies,
):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    payment_repository = Mock()
    customer_service.payment_repository = payment_repository
    payment_repository.find_by_reference.return_value = None

    request_id = uuid4()

    payment = Payment(
        maintenance_request_id=request_id,
        amount=50000,
        method=PaymentMethod.TRANSFER,
        reference="PAY-12345",
    )

    maintenance_request_repository.find_by_id.return_value = None

    with pytest.raises(AppException, match="Maintenance request not found"):
        customer_service.make_payment(payment)

    payment_repository.create.assert_not_called()




def test_make_payment_raises_error_when_request_is_cancelled(
    customer_service_dependencies,
):
    (
        customer_service,
        car_repository,
        maintenance_request_repository,
    ) = customer_service_dependencies

    payment_repository = Mock()
    customer_service.payment_repository = payment_repository
    payment_repository.find_by_reference.return_value = None

    request_id = uuid4()

    maintenance_request = MaintenanceRequest(
        car_id=uuid4(),
        description="Oil change",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.CANCELED,
    )

    maintenance_request.id = request_id

    payment = Payment(
        maintenance_request_id=request_id,
        amount=50000,
        method=PaymentMethod.TRANSFER,
        reference="PAY-12345",
    )

    maintenance_request_repository.find_by_id.return_value = (
        maintenance_request
    )

    with pytest.raises(
        AppException,
        match="Payment cannot be made for a cancelled request",
    ):
        customer_service.make_payment(payment)

    payment_repository.create.assert_not_called()



def test_make_payment_rejects_zero_amount(
    customer_service_dependencies,
):
    customer_service, car_repository, maintenance_request_repository = (
        customer_service_dependencies
    )

    payment_repository = Mock()
    customer_service.payment_repository = payment_repository

    maintenance_request = MaintenanceRequest(
        car_id=uuid4(),
        description="Engine problem",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.PENDING,
    )

    maintenance_request_repository.find_by_id.return_value = (
        maintenance_request
    )

    payment = Payment(
        maintenance_request_id=uuid4(),
        amount=Decimal("0"),
        method=PaymentMethod.TRANSFER,
        reference="PAY-001",
    )

    with pytest.raises(AppException, match="Payment amount must be greater than zero"):
        customer_service.make_payment(payment)

    payment_repository.create.assert_not_called()


def test_make_payment_rejects_negative_amount(
    customer_service_dependencies,
):
    customer_service, car_repository, maintenance_request_repository = (
        customer_service_dependencies
    )

    payment_repository = Mock()
    customer_service.payment_repository = payment_repository

    payment = Payment(
        maintenance_request_id=uuid4(),
        amount=Decimal("-100"),
        method=PaymentMethod.TRANSFER,
        reference="PAY-002",
    )

    with pytest.raises(
        AppException,
        match="Payment amount must be greater than zero",
    ):
        customer_service.make_payment(payment)

    payment_repository.create.assert_not_called()



def test_make_payment_rejects_duplicate_reference(
    customer_service_dependencies,
):
    customer_service, car_repository, maintenance_request_repository = (
        customer_service_dependencies
    )

    payment_repository = Mock()
    customer_service.payment_repository = payment_repository

    request_id = uuid4()

    maintenance_request = MaintenanceRequest(
        id=request_id,
        car_id=uuid4(),
        description="Engine problem",
        request_date=datetime.now(timezone.utc),
        status=MaintenanceStatus.PENDING,
    )

    maintenance_request_repository.find_by_id.return_value = (
        maintenance_request
    )

    payment_repository.find_by_reference.return_value = Payment(
        maintenance_request_id=request_id,
        amount=Decimal("50000"),
        method=PaymentMethod.TRANSFER,
        reference="PAY-001",
    )

    payment = Payment(
        maintenance_request_id=request_id,
        amount=Decimal("30000"),
        method=PaymentMethod.TRANSFER,
        reference="PAY-001",
    )

    with pytest.raises(
        AppException,
        match="Payment reference already exists",
    ):
        customer_service.make_payment(payment)

    payment_repository.create.assert_not_called()





def test_approve_work_successfully(
    customer_service_dependencies,
):
    service, user_repository, car_repository = (
        customer_service_dependencies
    )

    maintenance_service_repository = Mock(
        spec=MaintenanceServiceRepository
    )

    service.maintenance_service_repository = maintenance_service_repository

    maintenance_service = MaintenanceService(
        id=uuid4(),
        maintenance_request_id=uuid4(),
        name="Wheel alignment",
        description="Align all four wheels",
        cost=Decimal("15000.00"),
        is_additional=True,
        approval=ApprovalStatus.PENDING,
    )

    maintenance_service_repository.find_by_id.return_value = maintenance_service
    maintenance_service_repository.update.return_value = maintenance_service

    result = service.approve_work(maintenance_service.id)

    assert result.approval == ApprovalStatus.APPROVED