from datetime import datetime, date
from uuid import UUID

from sqlmodel import SQLModel, Field

from app.enums.maintenance_status import MaintenanceStatus


class MaintenanceRequestCreate(SQLModel):
    car_id: UUID
    description: str = Field(..., min_length=10 )
    request_date: datetime


class MaintenanceRequestResponse(SQLModel):
    id: UUID
    car_id: UUID
    description: str
    request_date: datetime
    status: MaintenanceStatus
    created_at: datetime
    updated_at: datetime
    completed_at: date | None = None
    next_service_date: date | None = None