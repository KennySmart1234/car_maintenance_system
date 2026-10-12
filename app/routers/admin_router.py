
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.enums.payment_transaction_status import PaymentTransactionStatus
from app.schemas.payment_schema import PaymentTransactionResponse
from app.services.paystack_payment_service import PaystackPaymentService
from app.config.dependencies import get_session, require_admin
from app.enums.maintenance_status import MaintenanceStatus
from app.models.maintenance_image import MaintenanceImage
from app.models.maintenance_service import MaintenanceService
from app.schemas.maintenance_service_schema import MaintenanceServiceCreate
from app.services.admin_service import AdminService
from app.schemas.maintenance_image_schema import (
    MaintenanceImageCreate,
    MaintenanceImageResponse,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@router.get("/verify-vehicle/{car_id}")
def verify_vehicle(
    car_id: UUID,
    plate_number: str,
    vin: str,
    session: Session = Depends(get_session)
):
    service = AdminService(session)
    return {
        "verified": service.verify_vehicle(car_id, plate_number, vin)
    }


@router.patch("/maintenance-requests/{request_id}/accept")
def accept_request(
    request_id: UUID,
    session: Session = Depends(get_session)
):
    service = AdminService(session)
    return service.accept_request(request_id)


@router.patch("/maintenance-requests/{request_id}/inspect")
def inspect_car(
    request_id: UUID,
    session: Session = Depends(get_session)
):
    service = AdminService(session)
    return service.inspect_car(request_id)


@router.post("/maintenance-services")
def add_service(
    service_data: MaintenanceServiceCreate,
    session: Session = Depends(get_session)
):
    maintenance_service = MaintenanceService(
        maintenance_request_id=service_data.maintenance_request_id,
        name=service_data.name,
        description=service_data.description,
        cost=service_data.cost,
        is_additional=service_data.is_additional
    )

    service = AdminService(session)
    return service.add_service(maintenance_service)


@router.patch("/maintenance-requests/{request_id}/status")
def update_status(
    request_id: UUID,
    status: MaintenanceStatus,
    session: Session = Depends(get_session)
):
    service = AdminService(session)
    return service.update_status(request_id, status)

@router.patch("/maintenance-requests/{request_id}/next-service-date")
def set_next_service_date(
    request_id: UUID,
    next_service_date: date,
    session: Session = Depends(get_session)
):
    service = AdminService(session)
    return service.set_next_service(request_id, next_service_date)


@router.post("/maintenance-images", response_model=MaintenanceImageResponse)
def upload_image(
    image_data: MaintenanceImageCreate,
    session: Session = Depends(get_session)
):
    image = MaintenanceImage(**image_data.model_dump())
    service = AdminService(session)
    return service.upload_image(image)

@router.post("/email-notifications/retry-failed")
def retry_failed_notifications(session: Session = Depends(get_session)):
    return AdminService(session).retry_failed_notifications()

@router.get(
    "/payment-transactions",
    response_model=list[PaymentTransactionResponse],
)
def list_payment_transactions(
    status: PaymentTransactionStatus = PaymentTransactionStatus.NEEDS_REVIEW,
    session: Session = Depends(get_session),
):
    """Online payments by status. Default: money received but not recorded."""
    return PaystackPaymentService(session).list_transactions(status)


@router.patch(
    "/payment-transactions/{reference}/resolve",
    response_model=PaymentTransactionResponse,
)
def resolve_payment_transaction(
    reference: str,
    session: Session = Depends(get_session),
):
    return PaystackPaymentService(session).resolve_transaction(reference)
