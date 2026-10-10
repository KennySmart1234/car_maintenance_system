from uuid import UUID

from sqlmodel import Session

from app.exceptions.app_exception import AppException
from app.models import Car

from app.repositories.car_repository import CarRepository
from app.repositories.maintenance_request_repository import MaintenanceRequestRepository


class CarService:
    def __init__(self, session: Session):
        self.car_repository = CarRepository(session)
        self.maintenance_request_repository = MaintenanceRequestRepository(session)



    def update_car_color(self, customer_id: UUID, car_id: UUID, color: str) -> Car:
        if not color or not color.strip():
            raise AppException("Color cannot be empty")

        car = self.car_repository.find_by_id(car_id)

        if car is None:
            raise AppException("Car not found")

        if car.customer_id != customer_id:
            raise AppException("You are not authorized to update this car")

        car.color = color.strip()

        return self.car_repository.update(car)


    def get_car_maintenance_history(self, car_id):
        car = self.car_repository.find_by_id(car_id)

        if car is None:
            raise AppException("Car not found")

        return self.maintenance_request_repository.find_by_car_id(car_id)