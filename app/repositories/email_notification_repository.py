
from uuid import UUID
from app.enums.email_status import EmailStatus

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.email_notification import EmailNotification


class EmailNotificationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self, notification: EmailNotification
    ) -> EmailNotification:
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        return notification

    def find_by_id(
        self, notification_id: UUID
    ) -> EmailNotification | None:
        statement = select(EmailNotification).where(
            EmailNotification.id == notification_id
        )
        return self.session.exec(statement).first()

    def find_by_user_id(
        self, user_id: UUID
    ) -> list[EmailNotification]:
        statement = select(EmailNotification).where(
            EmailNotification.user_id == user_id
        )
        return list(self.session.exec(statement).all())

    def update(
        self, notification: EmailNotification
    ) -> EmailNotification:
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        return notification

    def find_by_status(
        self, status: EmailStatus, limit: int = 100
    ) -> list[EmailNotification]:
        statement = (
            select(EmailNotification)
            .where(EmailNotification.status == status)
            .order_by(EmailNotification.id)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def count_by_status(self, status: EmailStatus) -> int:
        statement = select(func.count(EmailNotification.id)).where(
            EmailNotification.status == status
        )
        return self.session.exec(statement).one()

    def find_failed(self, limit: int = 50) -> list[EmailNotification]:
        statement = (
            select(EmailNotification)
            .where(EmailNotification.status == EmailStatus.FAILED)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())