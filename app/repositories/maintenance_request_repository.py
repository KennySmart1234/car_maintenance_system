from datetime import date
from uuid import UUID

from sqlmodel import Session, select, update

from app.enums.maintenance_status import MaintenanceStatus
from app.models.maintenance_request import MaintenanceRequest


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
        statement = select(MaintenanceRequest).where(MaintenanceRequest.car_id == car_id)
        return list(self.session.exec(statement).all())

    def find_all(self, status: MaintenanceStatus | None = None) -> list[MaintenanceRequest]:
        statement = select(MaintenanceRequest)

        if status is not None:
            statement = statement.where(MaintenanceRequest.status == status)

        statement = statement.order_by(
            MaintenanceRequest.created_at.desc())

        return list(self.session.exec(statement).all())


    def update(self, maintenance_request: MaintenanceRequest) -> MaintenanceRequest:
        self.session.add(maintenance_request)
        self.session.commit()
        self.session.refresh(maintenance_request)

        return maintenance_request

    def update_status_if_current(self, request_id: UUID,current_status: MaintenanceStatus,
            new_status: MaintenanceStatus, completed_at: date | None = None) -> MaintenanceRequest | None:
        values = {"status": new_status}

        if new_status == MaintenanceStatus.COMPLETED:
            values["completed_at"] = completed_at

        statement = (update(MaintenanceRequest).where(MaintenanceRequest.id == request_id,
                MaintenanceRequest.status == current_status).values(**values).returning(MaintenanceRequest))

        result = self.session.exec(statement).first()

        if result is None:
            self.session.rollback()
            return None
        self.session.commit()

        return result


    def delete(self, maintenance_request_id: UUID):
        self.session.delete(maintenance_request_id)
        self.session.commit()
        self.session.refresh(maintenance_request_id)