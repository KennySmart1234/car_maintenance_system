from uuid import UUID

from sqlalchemy import func, update
from sqlmodel import Session, select

from app.enums.notification_category import NotificationCategory
from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, notification: Notification) -> Notification:
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        return notification

    def find_by_id(self, notification_id: UUID) -> Notification | None:
        return self.session.get(Notification, notification_id)

    def find_for_user(
        self,
        user_id: UUID,
        category: NotificationCategory | None = None,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Notification]:
        statement = select(Notification).where(Notification.user_id == user_id)

        if category is not None:
            statement = statement.where(Notification.category == category)

        if unread_only:
            statement = statement.where(Notification.is_read.is_(False))

        statement = (
            statement.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def count_unread(self, user_id: UUID) -> int:
        statement = select(func.count(Notification.id)).where(
            Notification.user_id == user_id, Notification.is_read.is_(False)
        )
        return self.session.exec(statement).one()

    def save(self, notification: Notification) -> Notification:
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        return notification

    def mark_all_read(self, user_id: UUID) -> int:
        result = self.session.exec(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        self.session.commit()
        return result.rowcount
