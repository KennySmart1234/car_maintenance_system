from uuid import UUID

from sqlmodel import Session, select

from app.models.maintenance_request import MaintenanceRequest
from app.models.maintenance_service import MaintenanceService


class MaintenanceRequestRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, maintenance_request: MaintenanceRequest) -> MaintenanceRequest:
        self.session.add(maintenance_request)
        self.session.commit()
        self.session.refresh(maintenance_request)
        return maintenance_request


    def find_by_id(self, maintenance_request_id: UUID) -> MaintenanceRequest | None:
        statement = select(MaintenanceRequest).where(MaintenanceRequest.id == maintenance_request_id)
        return self.session.exec(statement).first()


    def find_by_car_id(self, car_id: UUID) -> list[MaintenanceRequest] | None:
        statement = select(MaintenanceRequest).where(MaintenanceRequest.id == car_id)
        return list(self.session.exec(statement).all())


    def update(self, maintenance_request: MaintenanceRequest) -> MaintenanceRequest:
        self.session.add(maintenance_request)
        self.session.commit()
        self.session.refresh(maintenance_request)

        return maintenance_request

    def delete(self, maintenance_request_id: UUID):
        self.session.delete(maintenance_request_id)
        self.session.commit()
        self.session.refresh(maintenance_request_id)