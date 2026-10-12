import json

from fastapi import APIRouter, Depends, Header, Request
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session

from app.config.access import assert_service_access
from app.config.dependencies import get_current_user, get_session, require_admin
from app.exceptions.app_exception import AppException
from app.models.payment import Payment
from app.models.user import User
from app.schemas.payment_schema import PaymentCreate, PaystackInitializeRequest
from app.services import paystack_service
from app.services.payment_service import PaymentService
from app.services.paystack_payment_service import PaystackPaymentService

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
    """Staff record a cash/POS/transfer payment they have confirmed."""
    payment = Payment(
        maintenance_request_id=payment_data.maintenance_request_id,
        maintenance_service_id=payment_data.maintenance_service_id,
        amount=payment_data.amount,
        method=payment_data.method
    )

    return PaymentService(session).create_payment(payment)


@router.post("/paystack/initialize")
def initialize_paystack_payment(
    data: PaystackInitializeRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    assert_service_access(session, data.maintenance_service_id, current_user)

    return PaystackPaymentService(session).start_payment(
        current_user, data.maintenance_service_id, data.amount
    )


@router.get("/paystack/callback")
def paystack_callback(
    reference: str,
    session: Session = Depends(get_session),
):
    """Where Paystack sends the customer's browser after paying.
    Public on purpose: we never trust the browser, we ask Paystack."""
    transaction = PaystackPaymentService(session).confirm_transaction(reference)

    messages = {
        "SUCCESS": "Payment received. Thank you!",
        "PENDING": "Payment not completed yet.",
        "NEEDS_REVIEW": "Payment received and is being reviewed by the workshop.",
        "RESOLVED": "Payment received and handled by the workshop.",
    }

    return {
        "status": transaction.status.value,
        "reference": transaction.reference,
        "message": messages[transaction.status.value],
    }


def _confirm_ignoring_unknown(session: Session, reference: str) -> None:
    try:
        PaystackPaymentService(session).confirm_transaction(reference)
    except AppException as error:
        if error.status_code != 404:  # unknown reference: not ours, ignore
            raise


@router.post("/paystack/webhook")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str | None = Header(default=None),
    session: Session = Depends(get_session),
):
    raw_body = await request.body()

    if not paystack_service.verify_signature(raw_body, x_paystack_signature):
        raise AppException("Invalid signature", status_code=401)

    try:
        event = json.loads(raw_body)
    except ValueError:
        raise AppException("Invalid payload", status_code=400)

    if event.get("event") == "charge.success":
        reference = (event.get("data") or {}).get("reference")

        if reference:
            await run_in_threadpool(_confirm_ignoring_unknown, session, reference)

    return {"status": "ok"}