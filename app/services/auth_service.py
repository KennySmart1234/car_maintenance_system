from datetime import datetime, timedelta, timezone
import secrets

from sqlmodel import Session
from app.config.password import DUMMY_HASH, hash_password, verify_password
from app.config.security import create_access_token
from app.config.settings import settings
from app.enums.user_role import UserRole
from app.exceptions.app_exception import AppException
from app.models.pending_registration import PendingRegistration
from app.models.user import User
from app.repositories.pending_registration_repository import PendingRegistrationRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate
from app.services.email_service import EmailService


def _as_utc(value: datetime) -> datetime:
    # Some databases return datetimes without timezone info.
    # We always store UTC, so treat a "naive" value as UTC.
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


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
            if _as_utc(existing_registration.expires_at) > datetime.now(timezone.utc):
                raise AppException(
                    "Registration already pending for this email. "
                    "Please check your email to verify."
                )
            # The old link expired: remove it so the person can register again.
            self.pending_registration_repository.delete(existing_registration)

        registration = PendingRegistration(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
            password=hash_password(user_data.password),
            verification_token=secrets.token_urlsafe(32),
            expires_at=datetime.now(timezone.utc)
                       + timedelta(minutes=settings.verification_token_expire_minutes),
        )

        registration = self.pending_registration_repository.create(registration)

        try:
            self.send_verification_email(registration)
        except Exception as error:
            # Don't leave a pending row behind that the person can't use.
            self.pending_registration_repository.delete(registration)
            print("EMAIL ERROR:", error)
            raise AppException(
                "We could not send the verification email. Please try again later.",
                status_code=503,
            )

        return registration

    def send_verification_email(self, registration: PendingRegistration):
        verification_url = (
            f"{settings.frontend_base_url}/verify-email"
            f"?token={registration.verification_token}"
        )

        EmailService().send_verification_email(
            registration.email,
            verification_url,
        )

    def verify_email(self, token: str) -> User:
        registration = self.pending_registration_repository.find_by_token(token)

        if registration is None:
            raise AppException("Invalid verification token", status_code=400)

        if _as_utc(registration.expires_at) < datetime.now(timezone.utc):
            raise AppException(
                "Verification link has expired. Please register again.",
                status_code=400,
            )

        if self.user_repository.find_by_email(registration.email) is not None:
            self.pending_registration_repository.delete(registration)
            raise AppException("Email already exists")

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


    def login(self, email: str, password: str) -> str:
        email = email.strip().lower()
        user = self.user_repository.find_by_email(email)

        if user is None:
            verify_password(password, DUMMY_HASH)  # same cost as a real check
            raise AppException("Invalid email or password", status_code=401)

        if not verify_password(password, user.password):
            raise AppException("Invalid email or password", status_code=401)

        if not user.email_verified:
            raise AppException("Email not verified", status_code=403)

        return create_access_token(user.id, user.role)