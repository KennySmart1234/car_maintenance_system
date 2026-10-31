from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.config.access import (
    assert_car_access,
    assert_request_access,
    assert_service_access,
)
from app.config.dependencies import get_current_user, get_session
from app.models.user import User
from app.schemas.car_schema import CarColorUpdate, CarCreate
from app.schemas.maintenance_request_schema import MaintenanceRequestCreate
from app.schemas.user_schema import RegistrationResponse
from app.services.car_service import CarService
from app.services.customer_service import CustomerService
from app.services.maintenance_service_service import MaintenanceServiceService

router = APIRouter(prefix="/customer", tags=["customer"])


@router.post("/cars", response_model=RegistrationResponse)
def add_car(
    car_data: CarCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    CustomerService(session).add_car(current_user.id, car_data)
    return {"message": "Car successfully added"}


@router.get("/cars")
def get_cars(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return CustomerService(session).get_cars(current_user.id)


@router.post("/maintenance-requests")
def maintenance_request(
    request: MaintenanceRequestCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    assert_car_access(session, request.car_id, current_user)
    CustomerService(session).submit_request(request)
    return {"message": "Request Submitted"}


@router.patch("/maintenance-services/{service_id}/approve")
def approve_work(
    service_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    assert_service_access(session, service_id, current_user)
    return CustomerService(session).approve_work(service_id)


@router.patch("/maintenance-services/{service_id}/reject")
def reject_work(
    service_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    assert_service_access(session, service_id, current_user)
    return CustomerService(session).reject_work(service_id)


@router.get("/cars/{car_id}/maintenance-history")
def maintenance_history(
    car_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    assert_car_access(session, car_id, current_user)
    return CustomerService(session).view_history(car_id)


@router.get("/maintenance-services/{request_id}")
def get_maintenance_services(
    request_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    assert_request_access(session, request_id, current_user)
    return MaintenanceServiceService(session).get_services_by_request_id(request_id)


@router.patch("/cars/{car_id}/color")
def update_car_color(
    car_id: UUID,
    color_data: CarColorUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return CarService(session).update_car_color(
        customer_id=current_user.id,
        car_id=car_id,
        color=color_data.color,
    )