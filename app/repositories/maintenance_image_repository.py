
from uuid import UUID

from sqlmodel import Session, select

from app.models.maintenance_image import MaintenanceImage


class MaintenanceImageRepository:

    def __init__(self, session: Session):
        self.session = session

    def create(self, image: MaintenanceImage) -> MaintenanceImage:
        self.session.add(image)
        self.session.commit()
        self.session.refresh(image)
        return image

    def find_by_id(self, image_id: UUID) -> MaintenanceImage | None:
        statement = select(MaintenanceImage).where(
            MaintenanceImage.id == image_id
        )
        return self.session.exec(statement).first()

    def find_by_request_id(
        self, request_id: UUID
    ) -> list[MaintenanceImage]:
        statement = select(MaintenanceImage).where(
            MaintenanceImage.maintenance_request_id == request_id
        )
        return list(self.session.exec(statement).all())

    def delete_by_id(self, image_id: UUID) -> bool:
        image = self.find_by_id(image_id)

        if image is None:
            return False

        self.session.delete(image)
        self.session.commit()
        return True
