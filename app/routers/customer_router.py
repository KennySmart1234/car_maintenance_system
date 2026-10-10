from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import session
from sqlmodel import Session

from app.config.dependencies import get_session
from app.models import MaintenanceRequest

from app.schemas.car_schema import CarCreate, CarColorUpdate
from app.schemas.maintenance_request_schema import MaintenanceRequestCreate

from app.schemas.user_schema import RegistrationResponse
from app.services.car_service import CarService
from app.services.customer_service import CustomerService
from app.services.maintenance_service_service import MaintenanceServiceService

router = APIRouter(prefix="/customer", tags=["customer"])


@router.post("/add car", response_model=RegistrationResponse)
def add_car(
            customer_id: UUID,
            car_data: CarCreate,
            session: Session = Depends(get_session)
):

    customer_service = CustomerService(session=session)
    customer_service.add_car(customer_id, car_data)

    return {
        "message": "Car successfully added"
    }


@router.get("/get cars")
def get_cars(customer_id,
             session: Session = Depends(get_session)
):

    customer_service = CustomerService(session=session)

    return customer_service.get_cars(customer_id)



@router.post("/maintenance request")
def maintenance_request(request: MaintenanceRequestCreate,
                        session: Session = Depends(get_session)
                        ):

    customer_service = CustomerService(session=session)
    customer_service.submit_request(request)

    return {
        "message": "Request Submitted"
    }



@router.patch("/maintenance-services/{service_id}/approve")
def approve_work(
    service_id: UUID,
    session: Session = Depends(get_session)
):
    customer_service = CustomerService(session)

    return customer_service.approve_work(service_id)




@router.post("/maintenance history")
def maintenance_history(car_id: UUID,
                        session: Session = Depends(get_session)
                        ):

    customer_service = CustomerService(session=session)
    return customer_service.view_history(car_id)



@router.get("/maintenance-services/{request_id}")
def get_maintenance_services(
    request_id: UUID,
    session: Session = Depends(get_session)
):
    service = MaintenanceServiceService(session)
    return service.get_services_by_request_id(request_id)



@router.patch("/cars/{car_id}/color")
def update_car_color(
    car_id: UUID,
    color_data: CarColorUpdate,
    customer_id: UUID,
    session: Session = Depends(get_session),
):
    car_service = CarService(session)

    return car_service.update_car_color(
        customer_id=customer_id,
        car_id=car_id,
        color=color_data.color,
    )