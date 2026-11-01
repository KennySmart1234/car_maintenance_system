from sqlalchemy import or_
from uuid import UUID

from sqlmodel import select

from app.enums.user_role import UserRole
from app.models.user import User


class UserRepository:

    def __init__(self, session):
        self.session = session


    def create(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def find_by_id(self, user_id: UUID) -> User | None:
        statement = select(User).where(User.id == user_id)
        return self.session.exec(statement).first()

    def find_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def find_by_role(self, role: UserRole) -> list[User]:
        statement = select(User).where(User.role == role).order_by(User.created_at)
        return list(self.session.exec(statement).all())

    def update(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user

    def delete(self, user: User) -> User:
        self.session.delete(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def search_by_role(
        self, role: UserRole, term: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[User]:
        statement = select(User).where(User.role == role)

        if term and term.strip():
            like = f"%{term.strip()}%"
            statement = statement.where(
                or_(
                    User.first_name.ilike(like),
                    User.last_name.ilike(like),
                    User.email.ilike(like),
                    User.phone.ilike(like),
                )
            )

        statement = statement.order_by(User.created_at.desc()).offset(offset).limit(limit)
        return list(self.session.exec(statement).all())
