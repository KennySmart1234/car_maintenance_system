from sqlalchemy import UUID
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, session: Session):
        self.user_repository = UserRepository(session)


    def get_user_by_id(self, user_id: UUID):
        return self.user_repository.find_by_id(user_id)

    def get_user_by_email(self, email: str):
        return self.user_repository.find_by_email(email)


    def create_user(self, user: User):
        return self.user_repository.create(user)