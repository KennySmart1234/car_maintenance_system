from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlmodel import SQLModel

from app.enums.maintenance_status import MaintenanceStatus
from app.enums.notification_category import NotificationCategory
from app.enums.payment_method import PaymentMethod


class CustomerCarSummary(SQLModel):
    id: UUID
    make: str
    model: str
    year: int
    plate_number: str


class CustomerRequestResponse(SQLModel):
    id: UUID
    description: str
    request_date: datetime
    status: MaintenanceStatus
    updated_at: datetime
    completed_at: date | None = None
    next_service_date: date | None = None
    car: CustomerCarSummary
    total_cost: Decimal
    total_paid: Decimal
    balance: Decimal
    pending_approval_count: int


class CustomerCarDetailResponse(SQLModel):
    id: UUID
    make: str
    model: str
    year: int
    color: str
    plate_number: str
    vin: str
    image_url: str | None = None
    created_at: datetime
    requests: list[CustomerRequestResponse]


class CustomerPaymentItem(SQLModel):
    reference: str
    maintenance_request_id: UUID
    request_description: str
    amount: Decimal
    date: datetime
    status: str  # SUCCESS, PENDING, FAILED, NEEDS_REVIEW
    method: PaymentMethod | None = None


class UnpaidService(SQLModel):
    service_id: UUID
    maintenance_request_id: UUID
    name: str
    balance: Decimal


class PaymentSummaryResponse(SQLModel):
    total_billed: Decimal
    total_paid: Decimal
    outstanding_balance: Decimal
    unpaid_services: list[UnpaidService]


class PaymentVerifyResponse(SQLModel):
    status: str
    reference: str
    amount: Decimal
    message: str


class NotificationResponse(SQLModel):
    id: UUID
    category: NotificationCategory
    title: str
    message: str
    maintenance_request_id: UUID | None = None
    is_read: bool
    created_at: datetime


class UnreadCountResponse(SQLModel):
    unread: int
