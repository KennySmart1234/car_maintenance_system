from uuid import UUID

from sqlmodel import Session, select
from app.models.email_notification import EmailNotification


class EmailNotificationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, notification: EmailNotification):
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        return notification

    def find_by_id(self, notification_id: UUID) -> EmailNotification | None:
        statement = select(EmailNotification).where(EmailNotification.id == notification_id)
        return self.session.exec(statement).first()

    def find_by_user_id(self, user_id: UUID) -> list[EmailNotification] | None:
        statement = select(EmailNotification).where(EmailNotification.user_id == user_id)
        return list(self.session.exec(statement).first())


    def update(self, notification: EmailNotification) -> EmailNotification:
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        return notification