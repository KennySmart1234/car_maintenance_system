from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlmodel import SQLModel

from app.enums.email_status import EmailStatus
from app.enums.maintenance_status import MaintenanceStatus
from app.enums.user_role import UserRole
from app.enums.image_category import ImageCategory
from app.enums.payment_method import PaymentMethod
from app.schemas.admin_maintenance_request_schema import (
    AdminCustomerResponse,
    AdminMaintenanceRequestResponse,
    AdminVehicleResponse,
)
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


class AdminCustomerListItem(AdminCustomerResponse):
    created_at: datetime
    vehicle_count: int


class AdminVehicleListItem(AdminVehicleResponse):
    owner_id: UUID
    owner_name: str


class AdminSearchResponse(SQLModel):
    requests: list[AdminMaintenanceRequestResponse]
    customers: list[AdminCustomerResponse]
    vehicles: list[AdminVehicleListItem]


class AdminPaymentListItem(SQLModel):
    id: UUID
    reference: str
    amount: Decimal
    method: PaymentMethod
    payment_date: datetime
    maintenance_request_id: UUID
    service_name: str | None = None
    customer_name: str
    plate_number: str


class AdminImageListItem(SQLModel):
    id: UUID
    maintenance_request_id: UUID
    image_url: str
    category: ImageCategory
    customer_name: str
    plate_number: str


class MonthlyRevenue(SQLModel):
    month: str
    revenue: Decimal


class TopService(SQLModel):
    name: str
    count: int
    revenue: Decimal


class AdminReportResponse(SQLModel):
    period_days: int
    total_revenue: Decimal
    requests_created: int
    revenue_by_month: list[MonthlyRevenue]
    requests_by_status: dict[str, int]
    payments_by_method: dict[str, Decimal]
    top_services: list[TopService]
