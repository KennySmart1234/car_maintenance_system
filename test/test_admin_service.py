from unittest.mock import Mock
from uuid import uuid4

from app.models.car import Car
from app.enums.maintenance_status import MaintenanceStatus
from app.repositories.maintenance_image_repository import MaintenanceImageRepository
from app.repositories.payment_repository import PaymentRepository
from app.services.admin_service import AdminService
from app.services.maintenance_request_service import MaintenanceRequestService
from app.repositories.car_repository import CarRepository
from app.services.maintenance_service_service import MaintenanceServiceService


def test_admin_can_verify_vehicle_when_plate_and_vin_match():
    car_id = uuid4()

    registered_car = Car(
        id=car_id,
        customer_id=uuid4(),
        plate_number="ABC-123",
        vin="1HGBH41JXMN109186",
    )

    car_repository = Mock(spec=CarRepository)
    car_repository.find_by_id.return_value = registered_car

    admin_service = AdminService.__new__(AdminService)
    admin_service.car_repository = car_repository

    result = admin_service.verify_vehicle(
        car_id=car_id,
        plate_number="ABC-123",
        vin="1HGBH41JXMN109186",
    )

    car_repository.find_by_id.assert_called_once_with(car_id)
    assert result is True



def test_admin_can_accept_maintenance_request():
    request_id = uuid4()
    expected_result = Mock()

    request_service = Mock(spec=MaintenanceRequestService)
    request_service.update_status.return_value = expected_result

    admin_service = AdminService.__new__(AdminService)
    admin_service.maintenance_request_service = request_service

    result = admin_service.accept_request(request_id)

    request_service.update_status.assert_called_once_with(
        request_id,
        MaintenanceStatus.ACCEPTED,
    )
    assert result == expected_result


def test_admin_cannot_verify_vehicle_when_plate_number_does_not_match():
    car_id = uuid4()

    registered_car = Car(
        id=car_id,
        customer_id=uuid4(),
        plate_number="ABC-123",
        vin="1HGBH41JXMN109186",
    )

    car_repository = Mock(spec=CarRepository)
    car_repository.find_by_id.return_value = registered_car

    admin_service = AdminService.__new__(AdminService)
    admin_service.car_repository = car_repository

    result = admin_service.verify_vehicle(
        car_id=car_id,
        plate_number="XYZ-999",
        vin="1HGBH41JXMN109186",
    )

    assert result is False


def test_admin_cannot_verify_vehicle_when_vin_does_not_match():
    car_id = uuid4()

    registered_car = Car(
        id=car_id,
        customer_id=uuid4(),
        plate_number="ABC-123",
        vin="1HGBH41JXMN109186",
    )

    car_repository = Mock(spec=CarRepository)
    car_repository.find_by_id.return_value = registered_car

    admin_service = AdminService.__new__(AdminService)
    admin_service.car_repository = car_repository

    result = admin_service.verify_vehicle(
        car_id=car_id,
        plate_number="ABC-123",
        vin="WRONG-VIN-123",
    )

    assert result is False


def test_admin_cannot_verify_vehicle_when_car_does_not_exist():
    car_id = uuid4()

    car_repository = Mock(spec=CarRepository)
    car_repository.find_by_id.return_value = None

    admin_service = AdminService.__new__(AdminService)
    admin_service.car_repository = car_repository

    result = admin_service.verify_vehicle(
        car_id=car_id,
        plate_number="ABC-123",
        vin="1HGBH41JXMN109186",
    )

    car_repository.find_by_id.assert_called_once_with(car_id)
    assert result is False


def test_admin_can_inspect_car():
    request_id = uuid4()
    expected_result = Mock()

    request_service = Mock(spec=MaintenanceRequestService)
    request_service.update_status.return_value = expected_result

    admin_service = AdminService.__new__(AdminService)
    admin_service.maintenance_request_service = request_service

    result = admin_service.inspect_car(request_id)

    request_service.update_status.assert_called_once_with(
        request_id,
        MaintenanceStatus.INSPECTING,
    )

    assert result == expected_result





def test_admin_can_add_maintenance_service():
    service_service = Mock(spec=MaintenanceServiceService)
    service = Mock()
    service.is_additional = True
    service.maintenance_request_id = uuid4()
    expected_result = service

    service_service.create_service.return_value = expected_result

    admin_service = AdminService.__new__(AdminService)
    admin_service.maintenance_service_service = service_service

    request_service = Mock(spec=MaintenanceRequestService)
    admin_service.maintenance_request_service = request_service

    result = admin_service.add_service(service)

    service_service.create_service.assert_called_once_with(service)
    assert result == expected_result

    request_service.update_status.assert_called_once_with(
        service.maintenance_request_id,
        MaintenanceStatus.AWAITING_APPROVAL,
    )


def test_admin_can_update_maintenance_request_status():
    request_id = uuid4()
    status = MaintenanceStatus.IN_PROGRESS
    expected_result = Mock()

    request_service = Mock(spec=MaintenanceRequestService)
    request_service.update_status.return_value = expected_result

    admin_service = AdminService.__new__(AdminService)
    admin_service.maintenance_request_service = request_service

    result = admin_service.update_status(request_id, status)

    request_service.update_status.assert_called_once_with(
        request_id,
        status,
    )
    assert result == expected_result


def test_admin_can_upload_maintenance_image():
    image = Mock()
    expected_result = Mock()

    image_repository = Mock(spec=MaintenanceImageRepository)
    image_repository.create.return_value = expected_result

    admin_service = AdminService.__new__(AdminService)
    admin_service.image_repository = image_repository

    result = admin_service.upload_image(image)

    image_repository.create.assert_called_once_with(image)
    assert result == expected_result



def test_admin_can_record_payment():
    payment = Mock()
    expected_result = Mock()

    payment_repository = Mock(spec=PaymentRepository)
    payment_repository.create.return_value = expected_result

    admin_service = AdminService.__new__(AdminService)
    admin_service.payment_repository = payment_repository

    result = admin_service.record_payment(payment)

    payment_repository.create.assert_called_once_with(payment)
    assert result == expected_result



def test_admin_service_initializes_payment_repository():
    session = Mock()

    admin_service = AdminService(session)

    assert admin_service.payment_repository is not None

