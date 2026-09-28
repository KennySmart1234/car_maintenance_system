
from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.enums.maintenance_status import MaintenanceStatus


class MaintenanceRequest(SQLModel, table=True):
    __tablename__ = "maintenance_requests"

    id: UUID = Field(default_factory=uuid4, primary_key = True)
    car_id:UUID = Field(foreign_key="cars.id")
    description: str
    request_date: datetime
    status: MaintenanceStatus = Field(default=MaintenanceStatus.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field( default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    next_service_date: date | None = None