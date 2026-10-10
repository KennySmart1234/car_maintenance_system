from pydantic import field_validator
from sqlmodel import SQLModel, Field


class CarCreate(SQLModel):
    make: str = Field(..., min_length=1, max_length=20)
    model: str = Field(..., min_length=1, max_length=20)
    year: int = Field(...)
    color: str = Field(..., min_length=1, max_length=20)
    plate_number: str = Field(..., min_length=1, max_length=20)
    vin: str = Field(..., min_length=1, max_length=20)


    @field_validator("make", "model", "color", "plate_number", "vin", mode="before")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        return value.strip()




class CarRegistrationResponse(SQLModel):
    message: str



class CarColorUpdate(SQLModel):
    color: str = Field(min_length=1, max_length=50)