from uuid import UUID

from sqlmodel import Session

from app.models.maintenance_image import MaintenanceImage
from app.enums.maintenance_status import MaintenanceStatus
from app.models.payment import Payment
from app.repositories.car_repository import CarRepository
from app.repositories.maintenance_image_repository import MaintenanceImageRepository
from app.repositories.payment_repository import PaymentRepository
from app.services.maintenance_request_service import MaintenanceRequestService
from app.services.maintenance_service_service import MaintenanceServiceService


class AdminService:
    def __init__(self, session: Session):
        self.car_repository = CarRepository(session)
        self.payment_repository = PaymentRepository(session)
        self.maintenance_request_service = MaintenanceRequestService(session)
        self.maintenance_service_service = MaintenanceServiceService(session)
        self.image_repository = MaintenanceImageRepository(session)

    def verify_vehicle(self, car_id: UUID, plate_number: str, vin: str) -> bool:
        car = self.car_repository.find_by_id(car_id)

        if car is None:
            return False

        return ( car.plate_number == plate_number
                and car.vin == vin)


    def accept_request(self, request_id: UUID):
        return self.maintenance_request_service.update_status(
            request_id, MaintenanceStatus.ACCEPTED)


    def inspect_car(self, request_id: UUID):
        return self.maintenance_request_service.update_status(
            request_id,
            MaintenanceStatus.INSPECTING,
        )

    def add_service(self, service):
        created_service = self.maintenance_service_service.create_service(service)

        if created_service.is_additional:
            self.maintenance_request_service.update_status(
                created_service.maintenance_request_id,
                MaintenanceStatus.AWAITING_APPROVAL,
            )

        return created_service

    def update_status(self, request_id: UUID, status: MaintenanceStatus):
        return self.maintenance_request_service.update_status(
            request_id, status)

    def upload_image(self, image: MaintenanceImage):
        return self.image_repository.create(image)


    def record_payment(self, payment: Payment):
        return self.payment_repository.create(payment)