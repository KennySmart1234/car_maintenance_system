
from _pydatetime import date, datetime
from dataclasses import field, Field
from uuid import UUID, uuid4

from sqlmodel import SQLModel

from app.enums.maintenance_status import MaintenanceStatus


class MaintenanceRequest(SQLModel, table=True):
    __tablename__ = "maintenance_requests"

    id: UUID = field(default_factory=uuid4, primary_key = True)
    car_id:UUID = Field(foreign_key="car.id")
    description: str
    request_date: datetime
    status: MaintenanceStatus = Field(default=MaintenanceStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utc.now)
    completed_at: datetime | None = None
    next_service_date: date | None = None