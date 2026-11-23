from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlmodel import Field, SQLModel
from pydantic import field_validator
from app.enums.approval_status import ApprovalStatus


class MaintenanceServiceCreate(SQLModel):
    maintenance_request_id: UUID
    name: str = Field(min_length=2, max_length=20)
    description: str = Field(min_length=5, max_length=100)
    cost: Decimal = Field(gt=0)
    is_additional: bool = False

    @field_validator("name", "description", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class MaintenanceServiceResponse(SQLModel):
    id: UUID
    maintenance_request_id: UUID
    name: str
    description: str
    cost: Decimal
    is_additional: bool
    approval: ApprovalStatus
    created_at: datetime
    approved_at: datetime | None
    updated_at: datetime | None