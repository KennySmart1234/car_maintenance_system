from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field

from app.enums.image_category import ImageCategory


class MaintenanceImage(SQLModel, table=True):
    __tablename__ = "maintenance_images"

    id : UUID = Field(default_factory = uuid4, primary_key=True)
    maintenance_request_id : UUID = Field(foreign_key = "maintenance_requests.id")
    image_url: str
    category : ImageCategory
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))