from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlmodel import Session

from app.config.access import assert_request_access
from app.config.dependencies import get_current_user, get_session, require_admin
from app.enums.maintenance_status import MaintenanceStatus
from app.models.maintenance_request import MaintenanceRequest
from app.models.user import User
from app.services.maintenance_request_service import MaintenanceRequestService


router = APIRouter(prefix="/maintenance-requests", tags=["maintenance requests"])


@router.get("/{request_id}", response_model=MaintenanceRequest)
def get_request_by_id(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return assert_request_access(session, request_id, current_user)


@router.patch("/{request_id}/status", response_model=MaintenanceRequest)
def update_request_status(
    request_id: UUID,
    status: MaintenanceStatus = Body(embed=True),
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    service = MaintenanceRequestService(session)
    return service.update_status(request_id, status)


@router.patch("/{request_id}/cancel", response_model=MaintenanceRequest)
def cancel_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    assert_request_access(session, request_id, current_user)
    service = MaintenanceRequestService(session)
    return service.cancel_request(request_id)


@router.get("/{request_id}/total-cost")
def calculate_total_cost(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict[str, Decimal]:
    assert_request_access(session, request_id, current_user)
    service = MaintenanceRequestService(session)

    return {"total_cost": service.calculate_total_cost(request_id)}


@router.get("/{request_id}/balance")
def calculate_balance(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict[str, Decimal]:
    assert_request_access(session, request_id, current_user)
    service = MaintenanceRequestService(session)

    return {"balance": service.calculate_balance(request_id)}


@router.patch("/{request_id}/next-service-date", response_model=MaintenanceRequest)
def update_next_service_date(
    request_id: UUID,
    next_service_date: date = Body(embed=True),
    _: User = Depends(require_admin),
    session: Session = Depends(get_session),
):
    service = MaintenanceRequestService(session)
    return service.update_next_service_date(request_id, next_service_date)