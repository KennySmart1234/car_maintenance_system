from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.enums.notification_category import NotificationCategory


class Notification(SQLModel, table=True):
    """An in-app message for a customer (separate from the email log)."""

    __tablename__ = "notifications"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    maintenance_request_id: UUID | None = Field(
        default=None, foreign_key="maintenance_requests.id"
    )
    category: NotificationCategory
    title: str
    message: str
    is_read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
