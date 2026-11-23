from uuid import UUID

from pydantic import field_validator
from sqlmodel import SQLModel, Field


class CarCreate(SQLModel):
    make: str = Field(..., min_length=1, max_length=20)
    model: str = Field(..., min_length=1, max_length=20)
    year: int = Field(...)
    color: str = Field(..., min_length=1, max_length=20)
    plate_number: str = Field(..., min_length=1, max_length=20)
    vin: str = Field(..., min_length=1, max_length=20)
    image_url: str | None = None


    @field_validator("make", "model", "color", "plate_number", "vin", mode="before")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        return value.strip()


class CarUpdate(SQLModel):
    """Details a customer may change on one of their cars. Send only what changed."""
    make: str | None = Field(default=None, min_length=1, max_length=20)
    model: str | None = Field(default=None, min_length=1, max_length=20)
    year: int | None = Field(default=None, ge=1886)
    color: str | None = Field(default=None, min_length=1, max_length=20)
    plate_number: str | None = Field(default=None, min_length=1, max_length=20)
    vin: str | None = Field(default=None, min_length=1, max_length=20)

    @field_validator("make", "model", "color", "plate_number", "vin", mode="before")
    @classmethod
    def strip_whitespace(cls, value):
        return value.strip() if isinstance(value, str) else value



class CarRegistrationResponse(SQLModel):
    message: str
    car_id: UUID



class CarColorUpdate(SQLModel):
    color: str = Field(min_length=1, max_length=50)