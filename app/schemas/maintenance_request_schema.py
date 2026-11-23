from datetime import datetime, date
from uuid import UUID

from sqlmodel import SQLModel, Field
from pydantic import field_validator

from app.enums.maintenance_status import MaintenanceStatus


from pydantic import AwareDatetime

class MaintenanceRequestCreate(SQLModel):
    car_id: UUID
    description: str = Field(..., min_length=10)
    request_date: AwareDatetime

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, value):
        # Trim first so spaces alone can never satisfy the minimum length.
        return value.strip() if isinstance(value, str) else value


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