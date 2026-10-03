from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class PendingRegistration(SQLModel, table=True):
    __tablename__ = "pending_registrations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    first_name: str
    last_name: str

    email: EmailStr = Field(unique=True, index=True)

    phone: str
    password: str

    verification_token: str = Field(unique=True, index=True)

    expires_at: datetime

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )