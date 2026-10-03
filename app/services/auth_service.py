from datetime import datetime, timedelta, timezone
import secrets

from app.config.password import hash_password, verify_password
from sqlmodel import Session
from app.config.security import create_access_token

from app.enums.user_role import UserRole
from app.exceptions.app_exception import AppException
from app.models.user import User
from app.models.pending_registration import PendingRegistration
from app.repositories.pending_registration_repository import PendingRegistrationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate
from app.services.email_service import EmailService


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)
        self.pending_registration_repository = PendingRegistrationRepository(session)

    def register_customer(self, user_data: UserCreate) -> PendingRegistration:
        existing_user = self.user_repository.find_by_email(user_data.email)

        if existing_user is not None:
            raise AppException("Email already exists")

        existing_registration = (
            self.pending_registration_repository.find_by_email(user_data.email)
        )

        if existing_registration is not None:
            raise AppException("Registration already pending for this email / Verify on your email")

        verification_token = secrets.token_urlsafe(32)

        registration = PendingRegistration(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
            password=hash_password(user_data.password),
            verification_token=verification_token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=4),
        )

        registration = self.pending_registration_repository.create(registration)

        self.send_verification_email(registration)

        return registration



    def send_verification_email(self, registration: PendingRegistration):
        verification_url = (
            f"http://192.168.0.112:8000/auth/verify-email"
            f"?token={registration.verification_token}"
        )

        EmailService().send_verification_email(
            registration.email,
            verification_url,
        )


    def verify_email(self, token: str) -> User:
        registration = (
            self.pending_registration_repository.find_by_token(token)
        )

        if registration is None:
            raise AppException("Invalid verification token")

        if registration.expires_at < datetime.now(timezone.utc):
            raise AppException("Verification token has expired")

        user = User(
            first_name=registration.first_name,
            last_name=registration.last_name,
            email=registration.email,
            phone=registration.phone,
            password=registration.password,
            role=UserRole.CUSTOMER,
            email_verified=True,
        )

        user = self.user_repository.create(user)

        self.pending_registration_repository.delete(registration)

        return user



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

