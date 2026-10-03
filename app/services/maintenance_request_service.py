from datetime  import date
from decimal import Decimal
from uuid import UUID

from sqlmodel import Session

from app.enums.approval_status import ApprovalStatus
from app.enums.maintenance_status import MaintenanceStatus
from app.exceptions.app_exception import AppException
from app.models.maintenance_request import MaintenanceRequest
from app.repositories.car_repository import CarRepository
from app.repositories.maintenance_request_repository import MaintenanceRequestRepository
from app.repositories.maintenance_service_repository import MaintenanceServiceRepository
from app.repositories.payment_repository import PaymentRepository



class MaintenanceRequestService:
    def __init__(self, session: Session):
        self.car_repository = CarRepository(session)
        self.maintenance_request_repository = MaintenanceRequestRepository(session)
        self.maintenance_service_repository = MaintenanceServiceRepository(session)
        self.payment_repository = PaymentRepository(session)


    def create_request(self, request: MaintenanceRequest) -> MaintenanceRequest:
        car = self.car_repository.find_by_id(request.car_id)

        if car is None:
            raise AppException("Car not found")

        return self.maintenance_request_repository.create(request)


    def get_request_by_id(self, request_id: UUID) -> MaintenanceRequest | None:
        request = self.maintenance_request_repository.find_by_id(request_id)
        if request is None:
            raise AppException("Maintenance request not found")
        return request


    def update_status(self, request_id: UUID, status: MaintenanceStatus):
        request = self.maintenance_request_repository.find_by_id(request_id)

        if request is None:
            raise AppException("Maintenance request not found")

        allowed_transitions = {
            MaintenanceStatus.PENDING: [MaintenanceStatus.ACCEPTED],
            MaintenanceStatus.ACCEPTED: [MaintenanceStatus.INSPECTING],
            MaintenanceStatus.INSPECTING: [MaintenanceStatus.AWAITING_APPROVAL, MaintenanceStatus.IN_PROGRESS],
            MaintenanceStatus.AWAITING_APPROVAL: [MaintenanceStatus.IN_PROGRESS],
            MaintenanceStatus.IN_PROGRESS: [MaintenanceStatus.COMPLETED],
        }

        if status not in allowed_transitions.get(request.status, []):
            raise AppException("Invalid maintenance status transition")

        request.status = status

        return self.maintenance_request_repository.update(request)


    def cancel_request(self, request_id: UUID):
        request = self.maintenance_request_repository.find_by_id(request_id)

        if request is None:
            raise AppException("Maintenance request not found")

        if request.status == MaintenanceStatus.COMPLETED:
            raise AppException("Completed maintenance request cannot be canceled")

        if request.status == MaintenanceStatus.CANCELED:
            raise AppException("Maintenance request is already canceled")

        request.status = MaintenanceStatus.CANCELED

        return self.maintenance_request_repository.update(request)


    def calculate_total_cost(self, request_id: UUID) -> Decimal:
        services = self.maintenance_service_repository.find_by_request_id(
            request_id
        )

        total = Decimal("0.00")

        for service in services:
            if not service.is_additional:
                total += service.cost

            elif service.approval == ApprovalStatus.APPROVED:
                total += service.cost

        return total


    def calculate_balance(self, request_id: UUID) -> Decimal:
        total_cost = self.calculate_total_cost(request_id)

        payments = self.payment_repository.find_by_request_id(request_id)

        total_paid = Decimal("0.00")

        for payment in payments:
            total_paid += payment.amount

        return total_cost - total_paid


    def update_next_service_date(self, request_id: UUID, date: date):
        request = self.maintenance_request_repository.find_by_id(request_id)

        if request is None:
            raise AppException("Maintenance request not found")

        request.next_service_date = date

        return self.maintenance_request_repository.update(request)



