
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlmodel import Session

from app.config.dependencies import get_session
from app.enums.maintenance_status import MaintenanceStatus
from app.models.maintenance_request import MaintenanceRequest
from app.services.maintenance_request_service import MaintenanceRequestService


router = APIRouter(prefix="/maintenance-requests", tags=["maintenance requests"]
)


@router.get("/{request_id}", response_model=MaintenanceRequest)
def get_request_by_id(
    request_id: UUID,
    session: Session = Depends(get_session)
):
    service = MaintenanceRequestService(session)
    return service.get_request_by_id(request_id)


@router.patch("/{request_id}/status", response_model=MaintenanceRequest)
def update_request_status(
    request_id: UUID,
    status: MaintenanceStatus = Body(embed=True),
    session: Session = Depends(get_session)
):
    service = MaintenanceRequestService(session)
    return service.update_status(request_id, status)


@router.patch("/{request_id}/cancel", response_model=MaintenanceRequest)
def cancel_request(
    request_id: UUID,
    session: Session = Depends(get_session)
):
    service = MaintenanceRequestService(session)
    return service.cancel_request(request_id)


@router.get("/{request_id}/total-cost")
def calculate_total_cost(
    request_id: UUID,
    session: Session = Depends(get_session)
) -> dict[str, Decimal]:
    service = MaintenanceRequestService(session)
    service.get_request_by_id(request_id)

    return {
        "total_cost": service.calculate_total_cost(request_id)
    }


@router.get("/{request_id}/balance")
def calculate_balance(
    request_id: UUID,
    session: Session = Depends(get_session)
) -> dict[str, Decimal]:
    service = MaintenanceRequestService(session)
    service.get_request_by_id(request_id)

    return {
        "balance": service.calculate_balance(request_id)
    }


@router.patch("/{request_id}/next-service-date",
              response_model=MaintenanceRequest)
def update_next_service_date(
    request_id: UUID,
    next_service_date: date = Body(embed=True),
    session: Session = Depends(get_session)
):
    service = MaintenanceRequestService(session)
    return service.update_next_service_date(
        request_id,
        next_service_date
    )
