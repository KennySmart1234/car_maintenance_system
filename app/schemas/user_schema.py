from pydantic import field_validator
from pydantic import EmailStr
from sqlmodel import SQLModel, Field


class UserCreate(SQLModel):
    first_name: str = Field(..., min_length=2, max_length=15)
    last_name: str = Field(..., min_length=2, max_length=15)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=10, max_length=20)
    phone: str = Field(..., min_length=11, max_length=14)


    @field_validator("first_name", "last_name", "phone", mode="before")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        return value.strip()

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower().strip()



