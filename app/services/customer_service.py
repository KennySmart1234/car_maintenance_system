from uuid import UUID

from sqlalchemy.orm import Session

from app.enums.approval_status import ApprovalStatus
from app.exceptions.app_exception import AppException
from app.models.car import Car
from app.models.maintenance_request import MaintenanceRequest
from app.models.payment import Payment
from app.services.payment_service import PaymentService
from app.repositories.car_repository import CarRepository
from app.repositories.maintenance_request_repository import MaintenanceRequestRepository
from app.repositories.maintenance_service_repository import MaintenanceServiceRepository
from app.repositories.user_repository import UserRepository
from app.schemas.maintenance_request_schema import MaintenanceRequestCreate


class CustomerService:
    def __init__(self, session: Session):
        self.maintenance_service_repository = MaintenanceServiceRepository(session)
        self.user_repository = UserRepository(session)
        self.car_repository = CarRepository(session)
        self.maintenance_request_repository = MaintenanceRequestRepository(session)
        self.payment_service = PaymentService(session)

    def add_car(self, car: Car)-> Car | None:
        existing_car = self.car_repository.find_by_plate_number(car.plate_number)

        if existing_car is not None:
            raise AppException("Plate number already exists")

        existing_car = self.car_repository.find_by_vin(car.vin)

        if existing_car is not None:
            raise AppException("VIN already exists")

        return self.car_repository.create(car)



    def get_cars(self, customer_id) -> list[Car] | None:
        return list(self.car_repository.find_by_customer_id(customer_id))


    def submit_request(self, request_data: MaintenanceRequestCreate):
        car = self.car_repository.find_by_id(request_data.car_id)

        if car is None:
            raise AppException("Car not found")

        maintenance_request = MaintenanceRequest(
            car_id=request_data.car_id,
            description=request_data.description,
            request_date=request_data.request_date,
        )

        return self.maintenance_request_repository.create(maintenance_request)


    def approve_work(self, service_id: UUID):
        service = self.maintenance_service_repository.find_by_id(service_id)

        if service is None:
            raise AppException("Maintenance service not found")

        if not service.is_additional:
            raise AppException("Only additional services require approval")

        if service.approval == ApprovalStatus.APPROVED:
            raise AppException("Maintenance service is already approved")

        if service.approval == ApprovalStatus.REJECTED:
            raise AppException("Rejected maintenance service cannot be approved")

        service.approval = ApprovalStatus.APPROVED

        return self.maintenance_service_repository.update(service)


    def view_history(self, car_id: UUID):
        return self.maintenance_request_repository.find_by_car_id(car_id)


    def make_payment(self, payment: Payment):
        return self.payment_service.create_payment(payment)


