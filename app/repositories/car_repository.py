from select import select
from uuid import UUID

from sqlmodel import Session

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


    def fnd_by_vin(self, vin: str) -> Car | None:
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
