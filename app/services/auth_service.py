
from sqlmodel import Session

from app.enums.user_role import UserRole
from app.exceptions.app_exception import AppException
from app.models.user import User
from app.repositories.email_verification_token_repository import EmailVerificationTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)
        self.token_repository = EmailVerificationTokenRepository(session)


    def register_customer(self, user_data: UserCreate) -> User:
        existing_user = self.user_repository.find_by_email(user_data.email)

        if existing_user is not None:
            raise AppException("Email already exists")

        user = User(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            password=user_data.password,
            phone=user_data.phone,
            role=UserRole.CUSTOMER,
        )

        return self.user_repository.create(user)
