from app.config.password import hash_password, verify_password
from sqlmodel import Session
from app.config.security import create_access_token

from app.enums.user_role import UserRole
from app.exceptions.app_exception import AppException
from app.models import user
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
            password=hash_password(user_data.password),
            phone=user_data.phone,
            role=UserRole.CUSTOMER,
        )

        return self.user_repository.create(user)



    def login(self, email: str, password: str) -> bool:
        email = email.strip().lower()
        user = self.user_repository.find_by_email(email)

        if user is None:
            raise AppException("Invalid email or password")

        if not verify_password(password, user.password):
            raise AppException("Invalid email or password")

        if not user.email_verified:
            raise AppException("Email not verified")

        access_token = create_access_token(user.id, user.role)

        return access_token

    def logout(self, email):
        email = email.strip().lower()

        user = self.user_repository.find_by_email(email)
        if user is None:
            raise AppException("Invalid email or password")

        return True

