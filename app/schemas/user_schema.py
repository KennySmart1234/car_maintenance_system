from datetime import datetime
from uuid import UUID

from pydantic import field_validator
from pydantic import EmailStr
from sqlmodel import SQLModel, Field

from app.enums.user_role import UserRole


class UserCreate(SQLModel):
    first_name: str = Field(..., min_length=2, max_length=15)
    last_name: str = Field(..., min_length=2, max_length=15)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=10, max_length=72)
    phone: str = Field(..., min_length=11, max_length=14)


    @field_validator("first_name", "last_name", "phone", mode="before")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        return value.strip()

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password is too long (maximum 72 bytes)")
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower().strip()



class RegistrationResponse(SQLModel):
    message: str


class UserResponse(SQLModel):
    id: UUID
    email: EmailStr
    role: UserRole
    email_verified: bool



class LoginRequest(SQLModel):
    email: EmailStr
    password: str



class LoginResponse(SQLModel):
    message: str



class ForgotPasswordRequest(SQLModel):
    email: EmailStr


class ResetPasswordRequest(SQLModel):
    token: str
    new_password: str = Field(..., min_length=10, max_length=72)

    @field_validator("new_password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password is too long (maximum 72 bytes)")
        return value


class UserProfileResponse(SQLModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    role: UserRole
    created_at: datetime


class ProfileUpdate(SQLModel):
    first_name: str | None = Field(default=None, min_length=2, max_length=15)
    last_name: str | None = Field(default=None, min_length=2, max_length=15)
    phone: str | None = Field(default=None, min_length=11, max_length=14)


class ChangePasswordRequest(SQLModel):
    current_password: str
    new_password: str = Field(..., min_length=10, max_length=72)


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
