from uuid import UUID

import select
from sqlmodel import Session

from app.models.maintenance_image import MaintenanceImage


class MaintenanceImageRepository:

    def __init__(self, session: Session):
        self.session = Session


    def create(self, image: MaintenanceImage):
        self.session.add(image)
        self.session.commit()
        self.session.refresh(image)
        return image

    def find_by_id(self, image_id: UUID) -> MaintenanceImage | None:
        statement = select(MaintenanceImage).where(MaintenanceImage.id == image_id)
        return self.session.exec(statement).first()

    def find_by_request_id(self, request_id: UUID) -> list[MaintenanceImage] | None:
        statement = select(MaintenanceImage).where(MaintenanceImage.id == request_id)
        return list(self.session.exec(statement).all())


    def delete_by_id(self, image_id: UUID):
        self.session.delete(image_id)

