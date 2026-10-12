from datetime import datetime
from uuid import UUID

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.enums.image_category import ImageCategory


class MaintenanceImageCreate(SQLModel):
    maintenance_request_id: UUID
    image_url: str = Field(min_length=1, max_length=500)
    category: ImageCategory

    @field_validator("image_url")
    @classmethod
    def must_be_http_url(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("image_url must start with http:// or https://")
        return value


class MaintenanceImageResponse(SQLModel):
    id: UUID
    maintenance_request_id: UUID
    image_url: str
    category: ImageCategory
    updated_at: datetime