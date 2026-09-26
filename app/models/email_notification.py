from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from app.enums.email_status import EmailStatus


class EmailNotification(SQLModel, table=True):
    __tablename__ = "email_notifications"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    user_id: UUID = Field(foreign_key="users.id")
    maintenance_request_id: UUID = Field(foreign_key="maintenance_requests.id")
    title: str
    subject: str
    message: str
    sent_at: datetime | None = None
    status: EmailStatus = Field(default=EmailStatus.PENDING)