from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.enums.approval_status import ApprovalStatus
from app.exceptions.app_exception import AppException
from app.models.car import Car
from app.models.maintenance_request import MaintenanceRequest
from app.models.payment import Payment
from app.repositories.payment_repository import PaymentRepository
from app.schemas.car_schema import CarCreate
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
        self.payment_repository = PaymentRepository(session)

    def add_car(self, customer_id:UUID, car_data: CarCreate)-> Car | None:
        existing_car = self.car_repository.find_by_plate_number(car_data.plate_number)

        if existing_car is not None:
            raise AppException("Plate number already exists")

        existing_car = self.car_repository.find_by_vin(car_data.vin)

        if existing_car is not None:
            raise AppException("VIN already exists")


        car = Car(
            customer_id=customer_id,
            make=car_data.make,
            model=car_data.model,
            year=car_data.year,
            color=car_data.color,
            plate_number=car_data.plate_number,
            vin=car_data.vin
        )

        return self.car_repository.create(car)



    def get_cars(self, customer_id: UUID) -> list[Car] | None:
        return self.car_repository.find_by_customer_id(customer_id)


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

        if service.approval != ApprovalStatus.PENDING:
            raise AppException("Maintenance service is not awaiting approval")

        service.approval = ApprovalStatus.APPROVED
        service.approved_at = datetime.now(timezone.utc)
        service.updated_at = datetime.now(timezone.utc)

        return self.maintenance_service_repository.update(service)



    def view_history(self, car_id: UUID):
        car = self.car_repository.find_by_id(car_id)

        if car is None:
            raise AppException("Car not found")

        requests = self.maintenance_request_repository.find_by_car_id(car_id)

        history = []

        for request in requests:
            services = self.maintenance_service_repository.find_by_request_id(
                request.id
            )

            service_history = []
            total_cost = 0
            total_paid = 0

            for service in services:

                if (
                        service.is_additional
                        and service.approval != ApprovalStatus.APPROVED
                ):
                    continue

                payments = self.payment_repository.find_by_service_id(
                    service.id
                )

                amount_paid = sum(
                    (payment.amount for payment in payments),
                    start=service.cost - service.cost,
                )

                balance = max(service.cost - amount_paid, 0)

                if amount_paid <= 0:
                    payment_status = "UNPAID"
                elif amount_paid < service.cost:
                    payment_status = "PARTIALLY_PAID"
                else:
                    payment_status = "PAID"

                service_history.append({
                    "service_id": service.id,
                    "service_name": service.name,
                    "description": service.description,
                    "cost": service.cost,
                    "payment": {
                        "status": payment_status,
                        "amount_paid": amount_paid,
                        "balance": balance,
                    },
                })

                total_cost += service.cost
                total_paid += amount_paid

            history.append({
                "request_id": request.id,
                "request_date": request.request_date,
                "request_status": request.status,
                "car": {
                    "car_id": car.id,
                    "make": car.make,
                    "model": car.model,
                    "year": car.year,
                    "plate_number": car.plate_number,
                },
                "services": service_history,
                "payment_summary": {
                    "total_cost": total_cost,
                    "total_paid": total_paid,
                    "outstanding_balance": max(
                        total_cost - total_paid, 0
                    ),
                },
            })

        return history

    def make_payment(self, payment: Payment):
        return self.payment_service.create_payment(payment)


