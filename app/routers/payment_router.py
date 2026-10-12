from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.config.access import assert_request_access
from app.config.dependencies import get_session, require_admin
from app.models import User
from app.models.payment import Payment
from app.schemas.payment_schema import PaymentCreate
from app.services.payment_service import PaymentService

router = APIRouter(
    prefix="/payments",
    tags=["payments"]
)


@router.post("/")
def make_payment(
    payment_data: PaymentCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    assert_request_access(session, payment_data.maintenance_request_id, current_user)

    payment = Payment(
        maintenance_request_id=payment_data.maintenance_request_id,
        maintenance_service_id=payment_data.maintenance_service_id,
        amount=payment_data.amount,
        method=payment_data.method
    )

    payment_service = PaymentService(session)

    return payment_service.create_payment(payment)