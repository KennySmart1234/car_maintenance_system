from datetime import date, datetime
from uuid import UUID

from sqlmodel import SQLModel

from app.enums.maintenance_status import MaintenanceStatus


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
    customer: AdminCustomerResponse
    vehicle: AdminVehicleResponse