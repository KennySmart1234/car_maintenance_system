import pytest

from unittest.mock import Mock

from app.exceptions.app_exception import AppException
from app.services.car_service import CarService


from uuid import uuid4

from app.models.car import Car


def test_add_car_with_complete_car_data():
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

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None
    car_repository.create.return_value = car

    result = car_service.add_car(car)

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

    car_service = CarService(session)
    car_service.car_repository = car_repository

    car = Mock()

    car_repository.find_by_plate_number.return_value = None
    car_repository.create.return_value = car
    car_repository.find_by_vin.return_value = None

    result = car_service.add_car(car)

    assert result == car

    car_repository.find_by_plate_number.assert_called_once_with(
        car.plate_number
    )

    car_repository.create.assert_called_once_with(car)



def test_add_car_rejects_duplicate_plate_number_with_complete_car():
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
        car_service.add_car(car)

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.find_by_vin.assert_not_called()
    car_repository.create.assert_not_called()



def test_add_car_when_plate_number_is_available():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    car = Mock()
    car.plate_number = "ABC-123"
    car.vin = "1HGCM82633A123456"

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None
    car_repository.create.return_value = car

    result = car_service.add_car(car)

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

    car_service = CarService(session)
    car_service.car_repository = car_repository

    existing_car = Mock()
    car_repository.find_by_plate_number.return_value = existing_car

    car = Mock()
    car.plate_number = "ABC-123"

    with pytest.raises(AppException, match="Plate number already exists"):
        car_service.add_car(car)

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.create.assert_not_called()




def test_add_car_rejects_duplicate_vin():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    existing_car = Mock()
    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = existing_car


    car = Mock()
    car.plate_number = "ABC-123"
    car.vin = "1HGCM82633A123456"

    with pytest.raises(AppException, match="VIN already exists"):
        car_service.add_car(car)

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.find_by_vin.assert_called_once_with(
        "1HGCM82633A123456"
    )

    car_repository.create.assert_not_called()


def test_add_car_rejects_duplicate_vin_with_complete_car():
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
        car_service.add_car(car)

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.find_by_vin.assert_called_once_with(
        "1HGCM82633A123456"
    )

    car_repository.create.assert_not_called()



def test_get_car_by_id_returns_car():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    car = Mock()
    car_id = "12345678-1234-1234-1234-123456789012"

    car_repository.find_by_id.return_value = car

    result = car_service.get_car_by_id(car_id)

    assert result == car

    car_repository.find_by_id.assert_called_once_with(car_id)


def test_add_car_checks_vin_after_plate_is_available():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    car = Mock()
    car.plate_number = "ABC-123"
    car.vin = "1HGCM82633A123456"

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None
    car_repository.create.return_value = car

    result = car_service.add_car(car)

    assert result == car

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.find_by_vin.assert_called_once_with(
        "1HGCM82633A123456"
    )

    car_repository.create.assert_called_once_with(car)



def test_add_car_accepts_unique_plate_and_vin():
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

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None
    car_repository.create.return_value = car

    result = car_service.add_car(car)

    assert result == car
    assert result.make == "Toyota"
    assert result.model == "Camry"
    assert result.year == 2022
    assert result.color == "Black"
    assert result.plate_number == "ABC-123"
    assert result.vin == "1HGCM82633A123456"

    car_repository.create.assert_called_once_with(car)



def test_add_car_rejects_duplicate_plate_and_vin():
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
        car_service.add_car(car)

    car_repository.find_by_plate_number.assert_called_once_with(
        "ABC-123"
    )

    car_repository.find_by_vin.assert_not_called()
    car_repository.create.assert_not_called()



def test_add_car_rejects_same_vin_with_different_plate():
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
        car_service.add_car(car)

    car_repository.create.assert_not_called()



def test_add_car_returns_car_from_repository():
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

    result = car_service.add_car(car)

    assert result is saved_car
    assert result is not car



def test_add_car_propagates_repository_create_error():
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

    car_repository.find_by_plate_number.return_value = None
    car_repository.find_by_vin.return_value = None

    car_repository.create.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        car_service.add_car(car)


def test_add_car_allows_different_customers_to_register_cars():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

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

    result_one = car_service.add_car(car_one)
    result_two = car_service.add_car(car_two)

    assert result_one == car_one
    assert result_two == car_two

    assert car_repository.create.call_count == 2



def test_get_car_by_id_returns_car():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    customer_id = uuid4()

    car = Car(
        customer_id=customer_id,
        make="Toyota",
        model="Camry",
        year=2022,
        color="Black",
        plate_number="ABC-123",
        vin="1HGCM82633A123456"
    )

    car_repository.find_by_id.return_value = car

    result = car_service.get_car_by_id(car.id)

    assert result == car

    car_repository.find_by_id.assert_called_once_with(car.id)



def test_get_car_by_id_returns_none_when_car_not_found():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    car_id = uuid4()

    car_repository.find_by_id.return_value = None

    result = car_service.get_car_by_id(car_id)

    assert result is None

    car_repository.find_by_id.assert_called_once_with(car_id)


def test_get_car_by_id_passes_id_to_repository():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    car_id = uuid4()

    car_repository.find_by_id.return_value = None

    result = car_service.get_car_by_id(car_id)

    assert result is None

    car_repository.find_by_id.assert_called_once_with(car_id)



def test_get_car_by_id_propagates_repository_error():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    car_id = uuid4()

    car_repository.find_by_id.side_effect = Exception(
        "Database error"
    )

    with pytest.raises(Exception, match="Database error"):
        car_service.get_car_by_id(car_id)

    car_repository.find_by_id.assert_called_once_with(car_id)


def test_get_customer_cars_returns_empty_list_when_customer_has_no_cars():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    customer_id = uuid4()

    car_repository.find_by_customer_id.return_value = []

    result = car_service.get_customer_cars(customer_id)

    assert result == []

    car_repository.find_by_customer_id.assert_called_once_with(
        customer_id
    )


def test_get_customer_cars_returns_single_car():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

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

    result = car_service.get_customer_cars(customer_id)

    assert result == [car]

    car_repository.find_by_customer_id.assert_called_once_with(
        customer_id
    )


def test_get_customer_cars_returns_only_repository_results():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

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

    result = car_service.get_customer_cars(customer_id)

    assert result == [customer_car]
    assert other_car not in result

    car_repository.find_by_customer_id.assert_called_once_with(
        customer_id
    )



def test_get_customer_cars_propagates_repository_error():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

    customer_id = uuid4()

    car_repository.find_by_customer_id.side_effect = Exception(
        "Database error"
    )

    with pytest.raises(Exception, match="Database error"):
        car_service.get_customer_cars(customer_id)

    car_repository.find_by_customer_id.assert_called_once_with(
        customer_id
    )




def test_get_customer_cars_returns_all_customer_cars():
    session = Mock()
    car_repository = Mock()

    car_service = CarService(session)
    car_service.car_repository = car_repository

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

    result = car_service.get_customer_cars(customer_id)

    assert result == [car_one, car_two]

    car_repository.find_by_customer_id.assert_called_once_with(
        customer_id
    )