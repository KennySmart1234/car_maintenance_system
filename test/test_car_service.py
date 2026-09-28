import pytest

from unittest.mock import Mock
from uuid import uuid4

from app.exceptions.app_exception import AppException
from app.models.car import Car
from app.services.car_service import CarService


def test_update_car_color_returns_updated_car():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    car = Car(
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    car_repository.find_by_id.return_value = car
    car_repository.update.return_value = car

    result = car_service.update_car_color(car.id, "Blue")

    assert result == car
    assert car.color == "Blue"

    car_repository.find_by_id.assert_called_once_with(car.id)
    car_repository.update.assert_called_once_with(car)



def test_update_car_color_raises_error_when_car_not_found():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    car_id = uuid4()

    car_repository.find_by_id.return_value = None

    with pytest.raises(AppException, match="Car not found"):
        car_service.update_car_color(car_id, "Blue")

    car_repository.find_by_id.assert_called_once_with(car_id)
    car_repository.update.assert_not_called()


def test_update_car_color_propagates_repository_error():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    car_id = uuid4()

    car_repository.find_by_id.side_effect = RuntimeError("Database error")

    with pytest.raises(RuntimeError, match="Database error"):
        car_service.update_car_color(car_id, "Blue")

    car_repository.find_by_id.assert_called_once_with(car_id)
    car_repository.update.assert_not_called()



def test_update_car_color_propagates_update_repository_error():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    car = Car(
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    car_repository.find_by_id.return_value = car
    car_repository.update.side_effect = RuntimeError("Database update error")

    with pytest.raises(RuntimeError, match="Database update error"):
        car_service.update_car_color(car.id, "Blue")

    assert car.color == "Blue"

    car_repository.find_by_id.assert_called_once_with(car.id)
    car_repository.update.assert_called_once_with(car)



@pytest.mark.parametrize(
    "invalid_color",
    [
        "",
        "   ",
    ]
)
def test_update_car_color_rejects_invalid_color(invalid_color):
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    car = Car(
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    car_repository.find_by_id.return_value = car

    with pytest.raises(AppException, match="Color cannot be empty"):
        car_service.update_car_color(car.id, invalid_color)

    assert car.color == "Black"
    car_repository.update.assert_not_called()



@pytest.mark.parametrize(
    "color",
    [
        "Blue",
        "  Blue  ",
        "Silver",
        "Black",
    ]
)
def test_update_car_color_accepts_valid_colors(color):
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    car = Car(
        customer_id=uuid4(),
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    car_repository.find_by_id.return_value = car
    car_repository.update.return_value = car

    result = car_service.update_car_color(car.id, color)

    assert result == car
    assert car.color == color.strip()

    car_repository.find_by_id.assert_called_once_with(car.id)
    car_repository.update.assert_called_once_with(car)


def test_get_car_maintenance_history_returns_maintenance_history():
    session = Mock()
    car_repository = Mock()
    maintenance_request_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository
    car_service.maintenance_request_repository = maintenance_request_repository

    car_id = uuid4()

    maintenance_history = [
        Mock(),
        Mock(),
    ]

    maintenance_request_repository.find_by_car_id.return_value = maintenance_history

    result = car_service.get_car_maintenance_history(car_id)

    assert result == maintenance_history

    maintenance_request_repository.find_by_car_id.assert_called_once_with(car_id)



def test_get_car_maintenance_history_raises_error_when_car_not_found():
    session = Mock()
    car_repository = Mock()
    maintenance_request_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository
    car_service.maintenance_request_repository = maintenance_request_repository

    car_id = uuid4()

    car_repository.find_by_id.return_value = None

    with pytest.raises(AppException, match="Car not found"):
        car_service.get_car_maintenance_history(car_id)

    car_repository.find_by_id.assert_called_once_with(car_id)


def test_get_car_maintenance_history_propagates_car_repository_error():
    session = Mock()
    car_repository = Mock()
    maintenance_request_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository
    car_service.maintenance_request_repository = maintenance_request_repository

    car_id = uuid4()

    error = Exception("Database error")
    car_repository.find_by_id.side_effect = error

    with pytest.raises(Exception, match="Database error"):
        car_service.get_car_maintenance_history(car_id)

    car_repository.find_by_id.assert_called_once_with(car_id)



def test_get_car_maintenance_history_propagates_maintenance_repository_error():
    session = Mock()
    car_repository = Mock()
    maintenance_request_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository
    car_service.maintenance_request_repository = maintenance_request_repository

    car_id = uuid4()

    car_repository.find_by_id.return_value = Mock()

    error = Exception("Database error")
    maintenance_request_repository.find_by_car_id.side_effect = error

    with pytest.raises(Exception, match="Database error"):
        car_service.get_car_maintenance_history(car_id)

    maintenance_request_repository.find_by_car_id.assert_called_once_with(car_id)


def test_get_car_maintenance_history_returns_empty_list_when_no_history():
    session = Mock()
    car_repository = Mock()
    maintenance_request_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository
    car_service.maintenance_request_repository = maintenance_request_repository

    car_id = uuid4()

    car_repository.find_by_id.return_value = Mock()
    maintenance_request_repository.find_by_car_id.return_value = []

    result = car_service.get_car_maintenance_history(car_id)

    assert result == []

    car_repository.find_by_id.assert_called_once_with(car_id)
    maintenance_request_repository.find_by_car_id.assert_called_once_with(car_id)


def test_get_car_maintenance_history_returns_all_records():
    session = Mock()
    car_repository = Mock()
    maintenance_request_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository
    car_service.maintenance_request_repository = maintenance_request_repository

    car_id = uuid4()

    car_repository.find_by_id.return_value = Mock()

    maintenance_history = [
        Mock(),
        Mock(),
        Mock(),
    ]

    maintenance_request_repository.find_by_car_id.return_value = maintenance_history

    result = car_service.get_car_maintenance_history(car_id)

    assert result == maintenance_history
    assert len(result) == 3

    maintenance_request_repository.find_by_car_id.assert_called_once_with(car_id)



def test_get_car_maintenance_history_does_not_query_history_when_car_not_found():
    session = Mock()
    car_repository = Mock()
    maintenance_request_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository
    car_service.maintenance_request_repository = maintenance_request_repository

    car_id = uuid4()

    car_repository.find_by_id.return_value = None

    with pytest.raises(AppException, match="Car not found"):
        car_service.get_car_maintenance_history(car_id)

    maintenance_request_repository.find_by_car_id.assert_not_called()