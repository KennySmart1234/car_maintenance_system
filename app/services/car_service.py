from uuid import UUID

from sqlmodel import Session

from app.exceptions.app_exception import AppException
from app.models.car import Car
from app.repositories.car_repository import CarRepository


class CarService:
    def __init__(self, session: Session):
        self.car_repository = CarRepository(session)

    def add_car(self, car: Car):
        existing_car = self.car_repository.find_by_plate_number(car.plate_number)

        if existing_car is not None:
            raise AppException("Plate number already exists")

        existing_car = self.car_repository.find_by_vin(car.vin)

        if existing_car is not None:
            raise AppException("VIN already exists")

        return self.car_repository.create(car)


    def get_car_by_id(self, car_id: UUID):
        return self.car_repository.find_by_id(car_id)


    def get_customer_cars(self, customer_id: UUID):
        return self.car_repository.find_by_customer_id(customer_id)


