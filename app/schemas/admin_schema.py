from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlmodel import SQLModel

from app.enums.email_status import EmailStatus
from app.enums.maintenance_status import MaintenanceStatus
from app.enums.user_role import UserRole
from app.schemas.payment_schema import PaymentTransactionResponse


class AdminUserResponse(SQLModel):
    """Safe view of an administrator. Never includes the password hash."""

    id: UUID
    first_name: str
    last_name: str
    email: str
    phone: str
    role: UserRole
    email_verified: bool
    created_at: datetime


class EmailNotificationResponse(SQLModel):
    id: UUID
    user_id: UUID
    recipient_email: str | None = None
    maintenance_request_id: UUID
    title: str
    subject: str
    status: EmailStatus
    sent_at: datetime | None = None


class RetryNotificationsResponse(SQLModel):
    sent: int
    still_failed: int


class DashboardRequestItem(SQLModel):
    id: UUID
    description: str
    status: MaintenanceStatus
    request_date: datetime
    updated_at: datetime
    customer_name: str
    plate_number: str
    vehicle: str
    pending_approval_count: int = 0


class DashboardStatistics(SQLModel):
    total_requests: int
    by_status: dict[str, int]
    created_last_30_days: int
    completed_last_30_days: int
    total_revenue: Decimal


class DashboardSection(SQLModel):
    count: int
    items: list[DashboardRequestItem]


class DashboardPaymentsSection(SQLModel):
    count: int
    items: list[PaymentTransactionResponse]


class DashboardNotificationsSection(SQLModel):
    failed_count: int


class DashboardActivityItem(SQLModel):
    request_id: UUID
    status: MaintenanceStatus
    description: str
    customer_name: str
    plate_number: str
    occurred_at: datetime


class AdminDashboardResponse(SQLModel):
    statistics: DashboardStatistics
    pending_work: DashboardSection
    awaiting_customer_approval: DashboardSection
    payments_needing_review: DashboardPaymentsSection
    notification_problems: DashboardNotificationsSection
    recent_activity: list[DashboardActivityItem]
