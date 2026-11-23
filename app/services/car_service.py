from datetime import timezone, datetime
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
            raise AppException("Color cannot be empty", status_code=400)

        car = self.car_repository.find_by_id(car_id)

        if car is None:
            raise AppException("Car not found", status_code=404)

        if car.customer_id != customer_id:
            raise AppException("You are not authorized to update this car", status_code=403)

        car.color = color.strip()

        return self.car_repository.update(car)


    def get_car_maintenance_history(self, car_id):
        car = self.car_repository.find_by_id(car_id)

        if car is None:
            raise AppException("Car not found", status_code=404)

        return self.maintenance_request_repository.find_by_car_id(car_id)



    def _owned_car(self, customer_id: UUID, car_id: UUID, action: str) -> Car:
        car = self.car_repository.find_by_id(car_id)

        if car is None:
            raise AppException("Car not found", status_code=404)

        if car.customer_id != customer_id:
            raise AppException(f"You are not authorized to {action} this car", status_code=403)

        return car

    def update_car(self, customer_id: UUID, car_id: UUID, data: CarUpdate) -> Car:
        car = self._owned_car(customer_id, car_id, "update")

        changes = data.model_dump(exclude_none=True)

        if not changes:
            raise AppException("No changes were supplied", status_code=400)

        newest_year = datetime.now(timezone.utc).year + 1
        if "year" in changes and changes["year"] > newest_year:
            raise AppException(f"Year cannot be later than {newest_year}", status_code=400)

        if "plate_number" in changes and changes["plate_number"] != car.plate_number:
            other = self.car_repository.find_by_plate_number(changes["plate_number"])
            if other is not None and other.id != car.id:
                raise AppException("Plate number already exists")

        if "vin" in changes and changes["vin"] != car.vin:
            other = self.car_repository.find_by_vin(changes["vin"])
            if other is not None and other.id != car.id:
                raise AppException("VIN already exists")

        for field, value in changes.items():
            setattr(car, field, value)

        car.updated_at = datetime.now(timezone.utc)

        return self.car_repository.update(car)

    def delete_car(self, customer_id: UUID, car_id: UUID) -> None:
        car = self._owned_car(customer_id, car_id, "delete")

        # Maintenance history must never be lost (PRD rule 8)
        if self.maintenance_request_repository.find_by_car_id(car_id):
            raise AppException(
                "This vehicle has service history and cannot be deleted. "
                "Its maintenance records are kept.",
                status_code=409,
            )

        photo_url = car.image_url
        self.car_repository.delete(car)

        if photo_url:
            image_storage.delete_image_file(photo_url)