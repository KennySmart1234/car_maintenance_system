from uuid import UUID

from sqlmodel import select

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
