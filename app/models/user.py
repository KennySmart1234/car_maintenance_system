from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from app.enums.user_role import UserRole


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    first_name: str
    last_name: str
    email: EmailStr = Field(unique=True, index=True)
    phone: str
    password: str
    role: UserRole
    email_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))