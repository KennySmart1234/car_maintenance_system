
from uuid import UUID

from sqlmodel import Session, select

from app.enums.image_category import ImageCategory
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
        self, request_id: UUID, category: ImageCategory | None = None
    ) -> list[MaintenanceImage]:
        statement = select(MaintenanceImage).where(
            MaintenanceImage.maintenance_request_id == request_id
        )

        if category is not None:
            statement = statement.where(MaintenanceImage.category == category)

        statement = statement.order_by(MaintenanceImage.updated_at.asc())
        return list(self.session.exec(statement).all())

    def update(self, image: MaintenanceImage) -> MaintenanceImage:
        self.session.add(image)
        self.session.commit()
        self.session.refresh(image)
        return image

    def delete_by_id(self, image_id: UUID) -> bool:
        image = self.find_by_id(image_id)

        if image is None:
            return False

        self.session.delete(image)
        self.session.commit()
        return True

    def find_all(
        self,
        category: ImageCategory | None = None,
        request_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MaintenanceImage]:
        statement = select(MaintenanceImage)

        if category is not None:
            statement = statement.where(MaintenanceImage.category == category)

        if request_id is not None:
            statement = statement.where(
                MaintenanceImage.maintenance_request_id == request_id
            )

        statement = (
            statement.order_by(MaintenanceImage.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())
