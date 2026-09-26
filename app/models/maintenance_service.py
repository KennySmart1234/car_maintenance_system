import datetime
from dataclasses import Field
from decimal import Decimal
from uuid import UUID, uuid4

from sqlmodel import SQLModel

from app.enums.approval_status import ApprovalStatus


class MaintenanceService(SQLModel, table=True):
    __tablename__ = "maintenance_services"
    id: UUID = Field(default_factory=uuid4, primary_key = True)
    maintenance_request_id: UUID = Field(foreign_key="maintenance_requests.id")
    name: str
    description: str
    cost:Decimal
    is_additional : bool = False
    approval : ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    created_at: datetime = Field(default=datetime.datetime.utcnow)
    approved_at: datetime | None = None
    updated_at: datetime | None = None