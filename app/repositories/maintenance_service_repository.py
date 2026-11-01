from decimal import Decimal
from sqlalchemy import func
from uuid import UUID

from sqlmodel import Session, select

from app.models.maintenance_service import MaintenanceService


class MaintenanceServiceRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, maintenance_service: MaintenanceService) -> MaintenanceService:
        self.session.add(maintenance_service)
        self.session.commit()
        self.session.refresh(maintenance_service)
        return maintenance_service

    def find_by_id_for_update(self, service_id: UUID) -> MaintenanceService | None:
        statement = (
            select(MaintenanceService)
            .where(MaintenanceService.id == service_id)
            .with_for_update()
        )
        return self.session.exec(statement).first()

    def find_by_id(self, service_id: UUID) -> MaintenanceService | None:
        statement = select(MaintenanceService).where(MaintenanceService.id == service_id)
        return self.session.exec(statement).first()

    def find_by_request_id(self, request_id: UUID) -> list[MaintenanceService]:
        statement = select(MaintenanceService).where(MaintenanceService.maintenance_request_id == request_id)
        return list(self.session.exec(statement).all())

    def update(self, maintenance_service: MaintenanceService) -> MaintenanceService:
        self.session.add(maintenance_service)
        self.session.commit()
        self.session.refresh(maintenance_service)

        return maintenance_service

    def top_services(self, limit: int = 5) -> list[tuple[str, int, Decimal]]:
        statement = (
            select(
                MaintenanceService.name,
                func.count(MaintenanceService.id),
                func.coalesce(func.sum(MaintenanceService.cost), 0),
            )
            .group_by(MaintenanceService.name)
            .order_by(func.count(MaintenanceService.id).desc())
            .limit(limit)
        )
        return [(n, c, Decimal(r)) for n, c, r in self.session.exec(statement).all()]
