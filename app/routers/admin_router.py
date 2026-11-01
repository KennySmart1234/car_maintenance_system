from datetime import date
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, Form, Query, UploadFile
from sqlmodel import Session

from app.config.dependencies import get_session, require_admin
from app.config.settings import settings
from app.enums.email_status import EmailStatus
from app.enums.image_category import ImageCategory
from app.enums.maintenance_status import MaintenanceStatus
from app.enums.payment_transaction_status import PaymentTransactionStatus
from app.exceptions.app_exception import AppException
from app.models.maintenance_image import MaintenanceImage
from app.models.maintenance_service import MaintenanceService
from app.schemas.admin_maintenance_request_schema import (
    AdminAwaitingApprovalResponse,
    AdminCustomerDetailResponse,
    AdminMaintenanceRequestDetailResponse,
    AdminMaintenanceRequestResponse,
    AdminVehicleDetailResponse,
    InspectionNotesUpdate,
    VehicleVerificationResponse,
)
from app.schemas.admin_schema import (
    AdminCustomerListItem,
    AdminImageListItem,
    AdminPaymentListItem,
    AdminReportResponse,
    AdminSearchResponse,
    AdminVehicleListItem,
    AdminDashboardResponse,
    AdminUserResponse,
    EmailNotificationResponse,
    RetryNotificationsResponse,
)
from app.schemas.maintenance_image_schema import (
    MaintenanceImageCreate,
    MaintenanceImageResponse,
)
from app.schemas.maintenance_service_schema import MaintenanceServiceCreate
from app.schemas.payment_schema import PaymentTransactionResponse
from app.schemas.user_schema import UserCreate
from app.services.admin_service import AdminService
from app.services.admin_view_service import AdminViewService
from app.services.paystack_payment_service import PaystackPaymentService

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


# ---------------------------------------------------------------- dashboard

@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_dashboard(session: Session = Depends(get_session)):
    """Statistics, pending work, approvals awaited, payments to review,
    notification problems and recent activity in one call."""
    return AdminViewService(session).get_dashboard()


# ---------------------------------------------------------- administrators

@router.get("/admins", response_model=list[AdminUserResponse])
def list_admins(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    return AdminService(session).list_admins()[offset:offset + limit]


@router.post("/admins", response_model=AdminUserResponse)
def add_admin(
    user_data: UserCreate,
    session: Session = Depends(get_session),
):
    return AdminService(session).add_admin(user_data)


# ------------------------------------------------- maintenance requests

@router.get(
    "/maintenance-requests",
    response_model=list[AdminMaintenanceRequestResponse],
)
def get_all_maintenance_requests(
    status: MaintenanceStatus | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    return AdminService(session).get_all_maintenance_requests(status)[offset:offset + limit]


# Declared before /{request_id} so "awaiting-approval" is not parsed as an id.
@router.get(
    "/maintenance-requests/awaiting-approval",
    response_model=list[AdminAwaitingApprovalResponse],
)
def get_requests_awaiting_approval(session: Session = Depends(get_session)):
    """Open requests with additional services the customer has not answered."""
    return AdminViewService(session).get_awaiting_approval()


@router.get(
    "/maintenance-requests/{request_id}",
    response_model=AdminMaintenanceRequestDetailResponse,
)
def get_maintenance_request_detail(
    request_id: UUID,
    session: Session = Depends(get_session),
):
    """Request with customer, vehicle, services (and approval state),
    images, payments and cost totals."""
    return AdminViewService(session).get_request_detail(request_id)


@router.patch("/maintenance-requests/{request_id}/accept")
def accept_request(
    request_id: UUID,
    session: Session = Depends(get_session),
):
    return AdminService(session).accept_request(request_id)


@router.patch("/maintenance-requests/{request_id}/inspect")
def inspect_car(
    request_id: UUID,
    data: InspectionNotesUpdate | None = None,
    session: Session = Depends(get_session),
):
    """Start the inspection; optionally record initial findings."""
    return AdminService(session).inspect_car(
        request_id, data.notes if data else None
    )


@router.put("/maintenance-requests/{request_id}/inspection-notes")
def set_inspection_notes(
    request_id: UUID,
    data: InspectionNotesUpdate,
    session: Session = Depends(get_session),
):
    if data.notes is None:
        raise AppException("Inspection notes are required", status_code=400)

    return AdminService(session).set_inspection_notes(request_id, data.notes)


@router.patch("/maintenance-requests/{request_id}/status")
def update_status(
    request_id: UUID,
    status: MaintenanceStatus,
    session: Session = Depends(get_session),
):
    return AdminService(session).update_status(request_id, status)


@router.patch("/maintenance-requests/{request_id}/next-service-date")
def set_next_service_date(
    request_id: UUID,
    next_service_date: date,
    session: Session = Depends(get_session),
):
    return AdminService(session).set_next_service(request_id, next_service_date)


# --------------------------------------------------- customers & vehicles

@router.get("/customers/{customer_id}", response_model=AdminCustomerDetailResponse)
def get_customer(customer_id: UUID, session: Session = Depends(get_session)):
    return AdminViewService(session).get_customer(customer_id)


@router.get("/vehicles/{car_id}", response_model=AdminVehicleDetailResponse)
def get_vehicle(car_id: UUID, session: Session = Depends(get_session)):
    return AdminViewService(session).get_vehicle(car_id)


@router.get(
    "/verify-vehicle/{car_id}",
    response_model=VehicleVerificationResponse,
)
def verify_vehicle(
    car_id: UUID,
    plate_number: str,
    vin: str,
    session: Session = Depends(get_session),
):
    """Compare the plate number and VIN read off the car with the record.
    Case, spaces and hyphens are ignored. The result says which one differs."""
    return AdminService(session).check_vehicle(car_id, plate_number, vin)


# ------------------------------------------------------------- services

@router.post("/maintenance-services")
def add_service(
    service_data: MaintenanceServiceCreate,
    session: Session = Depends(get_session),
):
    maintenance_service = MaintenanceService(
        maintenance_request_id=service_data.maintenance_request_id,
        name=service_data.name,
        description=service_data.description,
        cost=service_data.cost,
        is_additional=service_data.is_additional,
    )

    return AdminService(session).add_service(maintenance_service)


# --------------------------------------------------------------- images
# Listing is GET /maintenance-requests/{id}/images (shared with the customer).

@router.post("/maintenance-images", response_model=MaintenanceImageResponse)
def upload_image(
    image_data: MaintenanceImageCreate,
    session: Session = Depends(get_session),
):
    """Attach an image that is already hosted somewhere (by URL)."""
    image = MaintenanceImage(**image_data.model_dump())
    return AdminService(session).upload_image(image)


@router.post(
    "/maintenance-images/upload",
    response_model=MaintenanceImageResponse,
    status_code=201,
)
def upload_image_file(
    maintenance_request_id: UUID = Form(...),
    category: ImageCategory = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """Upload a JPEG, PNG or WebP photo (multipart form)."""
    content = file.file.read(settings.max_image_bytes + 1)
    return AdminService(session).upload_image_file(
        maintenance_request_id, category, content
    )


@router.patch(
    "/maintenance-images/{image_id}/category",
    response_model=MaintenanceImageResponse,
)
def update_image_category(
    image_id: UUID,
    category: ImageCategory = Body(embed=True),
    session: Session = Depends(get_session),
):
    return AdminService(session).update_image_category(image_id, category)


# -------------------------------------------------------- notifications

@router.get(
    "/email-notifications",
    response_model=list[EmailNotificationResponse],
)
def list_email_notifications(
    status: EmailStatus = EmailStatus.FAILED,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    """Defaults to FAILED notifications (the problems)."""
    return AdminService(session).list_notifications(status)[offset:offset + limit]


@router.post(
    "/email-notifications/retry-failed",
    response_model=RetryNotificationsResponse,
)
def retry_failed_notifications(session: Session = Depends(get_session)):
    return AdminService(session).retry_failed_notifications()


@router.post(
    "/email-notifications/{notification_id}/retry",
    response_model=EmailNotificationResponse,
)
def retry_notification(
    notification_id: UUID,
    session: Session = Depends(get_session),
):
    return AdminService(session).retry_notification(notification_id)


# ------------------------------------------------------------- payments

@router.get(
    "/payment-transactions",
    response_model=list[PaymentTransactionResponse],
)
def list_payment_transactions(
    status: PaymentTransactionStatus = PaymentTransactionStatus.NEEDS_REVIEW,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    """Online payments by status. Default: money received but not recorded."""
    return PaystackPaymentService(session).list_transactions(status)[offset:offset + limit]


@router.patch(
    "/payment-transactions/{reference}/resolve",
    response_model=PaymentTransactionResponse,
)
def resolve_payment_transaction(
    reference: str,
    session: Session = Depends(get_session),
):
    return PaystackPaymentService(session).resolve_transaction(reference)


# ------------------------------------------- lists, search and reports

@router.get("/customers", response_model=list[AdminCustomerListItem])
def list_customers(
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    return AdminViewService(session).list_customers(search, limit, offset)


@router.get("/vehicles", response_model=list[AdminVehicleListItem])
def list_vehicles(
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    return AdminViewService(session).list_vehicles(search, limit, offset)


@router.get("/search", response_model=AdminSearchResponse)
def search_everything(
    q: str = Query(min_length=2, max_length=50),
    session: Session = Depends(get_session),
):
    """Top matches across requests, customers and vehicles."""
    return AdminViewService(session).search(q)


@router.get("/payments", response_model=list[AdminPaymentListItem])
def list_payments(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    """Every recorded payment (cash, transfer, card and online), newest first."""
    return AdminViewService(session).list_payments(limit, offset)


@router.get("/maintenance-images", response_model=list[AdminImageListItem])
def list_images(
    category: ImageCategory | None = None,
    request_id: UUID | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    """Gallery of all maintenance photos."""
    return AdminViewService(session).list_images(category, request_id, limit, offset)


@router.get("/reports", response_model=AdminReportResponse)
def get_report(
    days: int = Query(180, ge=7, le=730),
    session: Session = Depends(get_session),
):
    return AdminViewService(session).get_report(days)
