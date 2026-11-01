from sqlalchemy import or_
from app.models.car import Car
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import exists, func
from sqlmodel import Session, select, update

from app.enums.maintenance_status import MaintenanceStatus
from app.enums.approval_status import ApprovalStatus
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
        maintenance_request.updated_at = datetime.now(timezone.utc)
        self.session.add(maintenance_request)
        self.session.commit()
        self.session.refresh(maintenance_request)

        return maintenance_request

    def update_status_if_current(self, request_id: UUID,current_status: MaintenanceStatus,
            new_status: MaintenanceStatus, completed_at: date | None = None) -> MaintenanceRequest | None:
        values = {"status": new_status, "updated_at": datetime.now(timezone.utc)}

        if new_status == MaintenanceStatus.COMPLETED:
            values["completed_at"] = completed_at

        statement = (update(MaintenanceRequest).where(MaintenanceRequest.id == request_id,
                MaintenanceRequest.status == current_status).values(**values).returning(MaintenanceRequest))

        row = self.session.exec(statement).first()

        if row is None:
            self.session.rollback()
            return None

        self.session.commit()

        # UPDATE ... RETURNING hands back a Row wrapping the entity; unwrap it
        # so callers get a MaintenanceRequest (and it serialises properly).
        return row[0]


    def delete(self, maintenance_request_id: UUID):
        self.session.delete(maintenance_request_id)
        self.session.commit()
        self.session.refresh(maintenance_request_id)

    def find_by_statuses(
        self,
        statuses: list[MaintenanceStatus],
        limit: int | None = None,
        oldest_first: bool = False,
    ) -> list[MaintenanceRequest]:
        statement = select(MaintenanceRequest).where(
            MaintenanceRequest.status.in_(statuses)
        )
        order = (
            MaintenanceRequest.created_at.asc()
            if oldest_first
            else MaintenanceRequest.created_at.desc()
        )
        statement = statement.order_by(order)

        if limit is not None:
            statement = statement.limit(limit)

        return list(self.session.exec(statement).all())

    def count_by_status(self) -> dict[MaintenanceStatus, int]:
        statement = select(
            MaintenanceRequest.status, func.count(MaintenanceRequest.id)
        ).group_by(MaintenanceRequest.status)

        return {status: count for status, count in self.session.exec(statement).all()}

    def count_created_since(self, since: datetime) -> int:
        statement = select(func.count(MaintenanceRequest.id)).where(
            MaintenanceRequest.created_at >= since
        )
        return self.session.exec(statement).one()

    def count_completed_since(self, since: datetime) -> int:
        statement = select(func.count(MaintenanceRequest.id)).where(
            MaintenanceRequest.status == MaintenanceStatus.COMPLETED,
            MaintenanceRequest.updated_at >= since,
        )
        return self.session.exec(statement).one()

    def find_recently_updated(self, limit: int = 10) -> list[MaintenanceRequest]:
        statement = (
            select(MaintenanceRequest)
            .order_by(MaintenanceRequest.updated_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def find_awaiting_customer_approval(self) -> list[MaintenanceRequest]:
        """Open requests that still have an additional service the customer
        has not answered (neither approved nor rejected)."""
        has_pending_service = exists().where(
            MaintenanceService.maintenance_request_id == MaintenanceRequest.id,
            MaintenanceService.is_additional.is_(True),
            MaintenanceService.approval == ApprovalStatus.PENDING,
        )

        statement = (
            select(MaintenanceRequest)
            .where(
                MaintenanceRequest.status.notin_(
                    [MaintenanceStatus.COMPLETED, MaintenanceStatus.CANCELED]
                ),
                has_pending_service,
            )
            .order_by(MaintenanceRequest.updated_at.asc())
        )
        return list(self.session.exec(statement).all())

    def find_by_customer_id(self, customer_id: UUID) -> list[MaintenanceRequest]:
        statement = (
            select(MaintenanceRequest)
            .join(Car, Car.id == MaintenanceRequest.car_id)
            .where(Car.customer_id == customer_id)
            .order_by(MaintenanceRequest.request_date.desc())
        )
        return list(self.session.exec(statement).all())

    def search(self, term: str, limit: int = 5) -> list[MaintenanceRequest]:
        like = f"%{term.strip()}%"
        statement = (
            select(MaintenanceRequest)
            .join(Car, Car.id == MaintenanceRequest.car_id)
            .where(
                or_(
                    MaintenanceRequest.description.ilike(like),
                    Car.plate_number.ilike(like),
                    Car.vin.ilike(like),
                )
            )
            .order_by(MaintenanceRequest.created_at.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement).all())
