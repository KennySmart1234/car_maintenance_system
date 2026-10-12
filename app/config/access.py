from uuid import UUID

from sqlmodel import Session

from app.enums.user_role import UserRole
from app.exceptions.app_exception import AppException
from app.models.car import Car
from app.models.maintenance_request import MaintenanceRequest
from app.models.maintenance_service import MaintenanceService
from app.models.user import User
from app.repositories.car_repository import CarRepository
from app.repositories.maintenance_request_repository import MaintenanceRequestRepository
from app.repositories.maintenance_service_repository import MaintenanceServiceRepository


def _is_admin(user: User) -> bool:
    return user.role == UserRole.WORKSHOP_ADMIN


def assert_car_access(session: Session, car_id: UUID, user: User) -> Car:
    car = CarRepository(session).find_by_id(car_id)

    if car is None:
        raise AppException("Car not found", status_code=404)

    if not _is_admin(user) and car.customer_id != user.id:
        raise AppException("You do not have access to this car", status_code=403)

    return car


def assert_request_access(
    session: Session, request_id: UUID, user: User
) -> MaintenanceRequest:
    request = MaintenanceRequestRepository(session).find_by_id(request_id)

    if request is None:
        raise AppException("Maintenance request not found", status_code=404)

    assert_car_access(session, request.car_id, user)
    return request


def assert_service_access(
    session: Session, service_id: UUID, user: User
) -> MaintenanceService:
    service = MaintenanceServiceRepository(session).find_by_id(service_id)

    if service is None:
        raise AppException("Maintenance service not found", status_code=404)

    assert_request_access(session, service.maintenance_request_id, user)
    return service