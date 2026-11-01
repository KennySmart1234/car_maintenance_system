"""In-app notifications for customers. Creating one never breaks the action
that triggered it: failures are logged and swallowed."""

from uuid import UUID

from sqlmodel import Session

from app.enums.maintenance_status import MaintenanceStatus
from app.enums.notification_category import NotificationCategory
from app.exceptions.app_exception import AppException
from app.models.notification import Notification
from app.repositories.car_repository import CarRepository
from app.repositories.maintenance_request_repository import MaintenanceRequestRepository
from app.repositories.notification_repository import NotificationRepository

STATUS_MESSAGES = {
    MaintenanceStatus.ACCEPTED: (
        "Maintenance Request Accepted",
        "Your maintenance request has been accepted by our team.",
    ),
    MaintenanceStatus.INSPECTING: (
        "Inspection Started",
        "We have started inspecting your vehicle.",
    ),
    MaintenanceStatus.IN_PROGRESS: (
        "Work In Progress",
        "Work on your vehicle has started.",
    ),
    MaintenanceStatus.COMPLETED: (
        "Maintenance Completed",
        "Your vehicle is ready. Thank you for choosing Motora.",
    ),
    MaintenanceStatus.CANCELED: (
        "Request Canceled",
        "Your maintenance request has been canceled.",
    ),
}


class NotificationService:
    def __init__(self, session: Session):
        self.repository = NotificationRepository(session)
        self.request_repository = MaintenanceRequestRepository(session)
        self.car_repository = CarRepository(session)

    # ---- creating ------------------------------------------------------

    def notify_request_customer(
        self,
        request_id: UUID,
        category: NotificationCategory,
        title: str,
        message: str,
    ) -> None:
        try:
            request = self.request_repository.find_by_id(request_id)
            car = self.car_repository.find_by_id(request.car_id)
            self.repository.create(
                Notification(
                    user_id=car.customer_id,
                    maintenance_request_id=request_id,
                    category=category,
                    title=title,
                    message=message,
                )
            )
        except Exception as error:  # never break the caller
            print("NOTIFICATION ERROR:", error)

    def notify_status_change(self, request_id: UUID, status: MaintenanceStatus) -> None:
        text = STATUS_MESSAGES.get(status)

        if text:
            self.notify_request_customer(
                request_id, NotificationCategory.MAINTENANCE, *text
            )

    # ---- reading -------------------------------------------------------

    def list_for_user(
        self,
        user_id: UUID,
        category: NotificationCategory | None,
        unread_only: bool,
        limit: int,
        offset: int,
    ) -> list[Notification]:
        return self.repository.find_for_user(
            user_id, category, unread_only, limit, offset
        )

    def unread_count(self, user_id: UUID) -> int:
        return self.repository.count_unread(user_id)

    def mark_read(self, user_id: UUID, notification_id: UUID) -> Notification:
        notification = self.repository.find_by_id(notification_id)

        if notification is None or notification.user_id != user_id:
            raise AppException("Notification not found", status_code=404)

        notification.is_read = True
        return self.repository.save(notification)

    def mark_all_read(self, user_id: UUID) -> int:
        return self.repository.mark_all_read(user_id)
