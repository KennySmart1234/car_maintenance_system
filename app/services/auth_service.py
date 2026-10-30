from datetime import datetime, timedelta, timezone
import secrets

from sqlmodel import Session
from app.config.password import DUMMY_HASH, hash_password, verify_password
from app.config.security import create_access_token
from app.config.settings import settings
from app.enums.user_role import UserRole
from app.exceptions.app_exception import AppException
from app.models.password_reset_token import PasswordResetToken
from app.models.pending_registration import PendingRegistration
from app.models.user import User
from app.repositories.pending_registration_repository import PendingRegistrationRepository
from app.repositories.password_reset_token_repository import PasswordResetTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate
from app.services.email_service import EmailService


def _as_utc(value: datetime) -> datetime:

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.user_repository = UserRepository(session)
        self.pending_registration_repository = PendingRegistrationRepository(session)
        self.password_reset_token_repository = PasswordResetTokenRepository(session)

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

            self.pending_registration_repository.delete(existing_registration)

        registration = PendingRegistration(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            phone=user_data.phone,
            password=hash_password(user_data.password).strip(),
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
        email = email.strip().lower().strip()
        password.strip()
        user = self.user_repository.find_by_email(email)

        if user is None:
            verify_password(password, DUMMY_HASH)  # same cost as a real check
            raise AppException("Invalid email or password", status_code=401)

        if not verify_password(password, user.password):
            raise AppException("Invalid email or password", status_code=401)

        if not user.email_verified:
            raise AppException("Email not verified", status_code=403)

        return create_access_token(user.id, user.role)



    def forgot_password(self, email: str) -> None:
        email = email.strip().lower()

        user = self.user_repository.find_by_email(email)

        if user is None or not user.email_verified:
            return

        token = secrets.token_urlsafe(32)

        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(
                    minutes=settings.password_reset_token_expire_minutes
                )
            ),
        )

        self.password_reset_token_repository.create(reset_token)

        reset_url = (
            f"{settings.frontend_base_url}/reset-password"
            f"?token={token}"
        )

        EmailService().send_password_reset_email(user.email, reset_url)


    def reset_password(self, token: str, new_password: str) -> None:
        reset_token = self.password_reset_token_repository.find_by_token(token)

        if reset_token is None:
            raise AppException(
                "Invalid password reset token",
                status_code=400,
            )

        if reset_token.used:
            raise AppException(
                "Password reset token has already been used",
                status_code=400,
            )

        if _as_utc(reset_token.expires_at) < datetime.now(timezone.utc):
            raise AppException(
                "Password reset token has expired",
                status_code=400,
            )

        user = self.user_repository.find_by_id(reset_token.user_id)

        if user is None:
            raise AppException(
                "Invalid password reset token",
                status_code=400,
            )

        user.password = hash_password(new_password)

        self.user_repository.update(user)

        reset_token.used = True

        self.password_reset_token_repository.update(reset_token)