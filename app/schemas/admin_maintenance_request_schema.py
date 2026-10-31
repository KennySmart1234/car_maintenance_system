from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlmodel import Field, SQLModel

from app.enums.maintenance_status import MaintenanceStatus
from app.enums.payment_method import PaymentMethod
from app.schemas.maintenance_image_schema import MaintenanceImageResponse
from app.schemas.maintenance_service_schema import MaintenanceServiceResponse


class AdminCustomerResponse(SQLModel):
    id: UUID
    first_name: str
    last_name: str
    email: str
    phone: str


class AdminVehicleResponse(SQLModel):
    id: UUID
    make: str
    model: str
    year: int
    color: str
    plate_number: str
    vin: str


class AdminMaintenanceRequestResponse(SQLModel):
    id: UUID
    description: str
    request_date: datetime
    status: MaintenanceStatus
    created_at: datetime
    updated_at: datetime
    completed_at: date | None = None
    next_service_date: date | None = None
    inspection_notes: str | None = None
    inspected_at: datetime | None = None
    customer: AdminCustomerResponse
    vehicle: AdminVehicleResponse


class AdminPaymentResponse(SQLModel):
    id: UUID
    maintenance_service_id: UUID | None = None
    amount: Decimal
    method: PaymentMethod
    reference: str
    payment_date: datetime


class AdminApprovalSummary(SQLModel):
    pending: int
    approved: int
    rejected: int


class AdminMaintenanceRequestDetailResponse(AdminMaintenanceRequestResponse):
    services: list[MaintenanceServiceResponse]
    images: list[MaintenanceImageResponse]
    payments: list[AdminPaymentResponse]
    approvals: AdminApprovalSummary
    total_cost: Decimal
    total_paid: Decimal
    balance: Decimal


class AdminAwaitingApprovalResponse(SQLModel):
    request: AdminMaintenanceRequestResponse
    pending_services: list[MaintenanceServiceResponse]
    approvals: AdminApprovalSummary


class AdminCustomerDetailResponse(SQLModel):
    customer: AdminCustomerResponse
    vehicles: list[AdminVehicleResponse]


class AdminVehicleDetailResponse(SQLModel):
    vehicle: AdminVehicleResponse
    owner: AdminCustomerResponse
    request_count: int


class InspectionNotesUpdate(SQLModel):
    notes: str | None = Field(default=None, min_length=1, max_length=2000)


class VehicleVerificationResponse(SQLModel):
    verified: bool
    car_found: bool
    plate_number_matches: bool
    vin_matches: bool
