from sqlalchemy import or_
from app.models.user import User

from uuid import UUID

from sqlmodel import Session, select

from app.models.car import Car


class CarRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, car: Car) -> Car:
        self.session.add(car)
        self.session.commit()
        self.session.refresh(car)

        return car

    def find_by_id(self, car_id: UUID) -> Car | None:
        statement = select(Car).where(Car.id == car_id)
        return self.session.exec(statement).first()


    def find_by_plate_number(self, plate_number: str) -> Car | None:
        statement = select(Car).where(Car.plate_number == plate_number)
        return self.session.exec(statement).first()


    def find_by_vin(self, vin: str) -> Car | None:
        statement = select(Car).where(Car.vin == vin)
        return self.session.exec(statement).first()


    def find_by_customer_id(self, customer_id: UUID) -> list[Car] | None:
        statement = select(Car).where(Car.customer_id == customer_id)
        return list(self.session.exec(statement).all())


    def update(self, car: Car) -> Car:
        self.session.add(car)
        self.session.commit()
        self.session.refresh(car)

        return car

    def search(self, term: str | None = None, limit: int = 100, offset: int = 0) -> list[Car]:
        statement = select(Car).join(User, User.id == Car.customer_id)

        if term and term.strip():
            like = f"%{term.strip()}%"
            statement = statement.where(
                or_(
                    Car.make.ilike(like),
                    Car.model.ilike(like),
                    Car.plate_number.ilike(like),
                    Car.vin.ilike(like),
                    User.first_name.ilike(like),
                    User.last_name.ilike(like),
                )
            )

        statement = statement.order_by(Car.created_at.desc()).offset(offset).limit(limit)
        return list(self.session.exec(statement).all())
