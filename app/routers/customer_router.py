from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlmodel import Session

from app.config.access import (
    assert_car_access,
    assert_request_access,
    assert_service_access,
)
from app.config.dependencies import get_current_user, get_session
from app.config.settings import settings
from app.enums.notification_category import NotificationCategory
from app.exceptions.app_exception import AppException
from app.models.user import User
from app.schemas.customer_schema import (
    CustomerCarDetailResponse,
    CustomerPaymentItem,
    CustomerRequestResponse,
    NotificationResponse,
    PaymentSummaryResponse,
    PaymentVerifyResponse,
    UnreadCountResponse,
)
from app.services.customer_portal_service import CustomerPortalService
from app.services.notification_service import NotificationService
from app.services.paystack_payment_service import PaystackPaymentService
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


# ------------------------------------------------ requests, cars, photo

@router.get("/maintenance-requests", response_model=list[CustomerRequestResponse])
def list_my_requests(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return CustomerPortalService(session).list_requests(current_user.id)


@router.get("/cars/{car_id}", response_model=CustomerCarDetailResponse)
def get_car_detail(
    car_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    car = assert_car_access(session, car_id, current_user)
    return CustomerPortalService(session).get_car_detail(car)


@router.post("/cars/{car_id}/photo", response_model=CustomerCarDetailResponse)
def upload_car_photo(
    car_id: UUID,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Add or replace the photo of one of my cars (JPEG, PNG or WebP)."""
    car = assert_car_access(session, car_id, current_user)
    content = file.file.read(settings.max_image_bytes + 1)
    portal = CustomerPortalService(session)
    return portal.get_car_detail(portal.set_car_photo(car, content))


# ------------------------------------------------------------ payments

@router.get("/payments", response_model=list[CustomerPaymentItem])
def list_my_payments(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return CustomerPortalService(session).list_payments(current_user.id)


@router.get("/payments/summary", response_model=PaymentSummaryResponse)
def my_payment_summary(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """What I still owe, with the services I can pay for (use them with
    POST /payments/paystack/initialize)."""
    return CustomerPortalService(session).payment_summary(current_user.id)


@router.get("/payments/verify/{reference}", response_model=PaymentVerifyResponse)
def verify_my_payment(
    reference: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Used by the Payment Success page: asks Paystack (never the browser)."""
    paystack = PaystackPaymentService(session)
    transaction = paystack.transaction_repository.find_by_reference(reference)

    if transaction is None or transaction.user_id != current_user.id:
        raise AppException("Payment transaction not found", status_code=404)

    transaction = paystack.confirm_transaction(reference)
    messages = {
        "SUCCESS": "Payment received. Thank you!",
        "PENDING": "Payment not completed yet.",
        "NEEDS_REVIEW": "Payment received and is being reviewed by the workshop.",
        "RESOLVED": "Payment received and handled by the workshop.",
        "FAILED": "Payment failed. You have not been charged.",
    }
    return PaymentVerifyResponse(
        status=transaction.status.value,
        reference=transaction.reference,
        amount=transaction.amount,
        message=messages.get(transaction.status.value, ""),
    )


# ------------------------------------------------------- notifications

@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications(
    category: NotificationCategory | None = None,
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return NotificationService(session).list_for_user(
        current_user.id, category, unread_only, limit, offset
    )


@router.get("/notifications/unread-count", response_model=UnreadCountResponse)
def unread_count(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return UnreadCountResponse(unread=NotificationService(session).unread_count(current_user.id))


@router.post("/notifications/read-all")
def mark_all_read(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return {"marked": NotificationService(session).mark_all_read(current_user.id)}


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_read(
    notification_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return NotificationService(session).mark_read(current_user.id, notification_id)
