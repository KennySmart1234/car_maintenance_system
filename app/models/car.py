from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class Car(SQLModel, table=True):
    __tablename__ = "cars"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    customer_id: UUID = Field(foreign_key="users.id")
    make: str
    model: str
    year: int
    color: str
    plate_number: str = Field(unique=True, index=True)
    vin:str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
