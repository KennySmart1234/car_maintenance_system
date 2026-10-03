from datetime import timezone, datetime, timedelta

import pytest
from unittest.mock import Mock, patch

from sqlmodel import Session, select

from app.config.database import engine
from app.config.password import hash_password
from app.enums.user_role import UserRole
from app.exceptions.app_exception import AppException
from app.models import User, PendingRegistration
from app.schemas.user_schema import UserCreate
from app.services.auth_service import AuthService


@pytest.fixture
def auth_service_setup():
    session = Mock()
    user_repository = Mock()
    pending_registration_repository = Mock()

    auth_service = AuthService(session)

    auth_service.user_repository = user_repository
    auth_service.pending_registration_repository = pending_registration_repository

    return auth_service, user_repository, pending_registration_repository


def test_register_customer_creates_pending_registration_not_user():
    user_data = UserCreate(
        first_name="Kenny",
        last_name="Olatunji",
        email="olatunjikenny@example.com",
        password="Password1234",
        phone="08012345678",
    )

    with Session(engine) as session:
        auth_service = AuthService(session)

        with patch(
            "app.services.auth_service.EmailService.send_verification_email"
        ):
            registration = auth_service.register_customer(user_data)

        user = session.exec(
            select(User).where(User.email == user_data.email)
        ).first()

        pending_registration = session.exec(
            select(PendingRegistration).where(
                PendingRegistration.email == user_data.email
            )
        ).first()

        assert user is None
        assert registration is not None
        assert pending_registration is not None
        assert pending_registration.email == user_data.email
        assert pending_registration.password != user_data.password
        assert pending_registration.verification_token is not None

        session.delete(pending_registration)
        session.commit()

def test_register_create_customer(auth_service_setup):
    auth_service, user_repository, pending_registration_repository = auth_service_setup

    user_data = UserCreate(
        first_name="smart",
        last_name="kenny",
        email="kennysmart@gmail.com",
        password="My_Password1234!",
        phone="+2348106086634"
    )

    user_repository.find_by_email.return_value = None
    pending_registration_repository.find_by_email.return_value = None
    pending_registration_repository.create.side_effect = lambda registration: registration

    with patch(
        "app.services.auth_service.EmailService.send_verification_email"
    ):
        registration = auth_service.register_customer(user_data)

    user_repository.find_by_email.assert_called_once_with(
        "kennysmart@gmail.com"
    )

    pending_registration_repository.find_by_email.assert_called_once_with(
        "kennysmart@gmail.com"
    )

    pending_registration_repository.create.assert_called_once()

    assert registration is not None
    assert registration.first_name == "smart"
    assert registration.last_name == "kenny"
    assert registration.email == "kennysmart@gmail.com"
    assert registration.phone == "+2348106086634"
    assert registration.verification_token is not None
    assert registration.password != user_data.password



def test_register_customer_rejects_existing_email(auth_service_setup):
    auth_service, user_repository, token_repository = auth_service_setup

    user_data = UserCreate(
        first_name="smart",
        last_name="kenny",
        email="kennysmart@gmail.com",
        password="My_Password1234!",
        phone="+2348106086634"
    )

    existing_user = Mock()
    user_repository.find_by_email.return_value = existing_user

    with pytest.raises(AppException, match="Email already exists"):
        auth_service.register_customer(user_data)

    user_repository.find_by_email.assert_called_once_with("kennysmart@gmail.com")
    user_repository.create.assert_not_called()



def test_verify_email_rejects_invalid_token(
    auth_service_setup,
):
    auth_service, user_repository, pending_registration_repository = (
        auth_service_setup
    )

    pending_registration_repository.find_by_token.return_value = None

    with pytest.raises(
        AppException,
        match="Invalid verification token",
    ):
        auth_service.verify_email("invalid-token")

    pending_registration_repository.find_by_token.assert_called_once_with(
        "invalid-token"
    )

    user_repository.create.assert_not_called()
    pending_registration_repository.delete.assert_not_called()


def test_verify_email_rejects_invalid_token(
    auth_service_setup,
):
    auth_service, user_repository, pending_registration_repository = (
        auth_service_setup
    )

    pending_registration_repository.find_by_token.return_value = None

    with pytest.raises(
        AppException,
        match="Invalid verification token",
    ):
        auth_service.verify_email("invalid-token")

    pending_registration_repository.find_by_token.assert_called_once_with(
        "invalid-token"
    )

    user_repository.create.assert_not_called()
    pending_registration_repository.delete.assert_not_called()


def test_verify_email_rejects_expired_token(
    auth_service_setup,
):
    auth_service, user_repository, pending_registration_repository = (
        auth_service_setup
    )

    pending_registration = PendingRegistration(
        first_name="smart",
        last_name="kenny",
        email="expired@example.com",
        phone="+2348106086634",
        password="hashed_password",
        verification_token="expired-token",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    pending_registration_repository.find_by_token.return_value = (
        pending_registration
    )

    with pytest.raises(
        AppException,
        match="Verification token has expired",
    ):
        auth_service.verify_email("expired-token")

    pending_registration_repository.find_by_token.assert_called_once_with(
        "expired-token"
    )

    user_repository.create.assert_not_called()
    pending_registration_repository.delete.assert_not_called()


def test_verify_email_does_not_create_user_before_token_is_valid(
    auth_service_setup,
):
    auth_service, user_repository, pending_registration_repository = (
        auth_service_setup
    )

    pending_registration_repository.find_by_token.return_value = None

    with pytest.raises(
        AppException,
        match="Invalid verification token",
    ):
        auth_service.verify_email("wrong-token")

    user_repository.create.assert_not_called()
    pending_registration_repository.delete.assert_not_called()


def test_verify_email_creates_customer_with_hashed_password(
    auth_service_setup,
):
    auth_service, user_repository, pending_registration_repository = (
        auth_service_setup
    )

    pending_registration = PendingRegistration(
        first_name="smart",
        last_name="kenny",
        email="password@example.com",
        phone="+2348106086634",
        password=hash_password("My_Password1234!"),
        verification_token="password-token",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )

    pending_registration_repository.find_by_token.return_value = (
        pending_registration
    )

    created_user = Mock()
    created_user.email = pending_registration.email
    created_user.email_verified = True
    created_user.role = UserRole.CUSTOMER

    user_repository.create.return_value = created_user

    result = auth_service.verify_email("password-token")

    created_user_argument = user_repository.create.call_args.args[0]

    assert result == created_user
    assert created_user_argument.password == pending_registration.password
    assert created_user_argument.password != "My_Password1234!"
    assert created_user_argument.email_verified is True
    assert created_user_argument.role == UserRole.CUSTOMER

    pending_registration_repository.delete.assert_called_once_with(
        pending_registration
    )


def test_verify_email_creates_verified_customer(
    auth_service_setup,
):
    auth_service, user_repository, pending_registration_repository = (
        auth_service_setup
    )

    pending_registration = PendingRegistration(
        first_name="smart",
        last_name="kenny",
        email="verify@example.com",
        phone="+2348106086634",
        password="hashed_password",
        verification_token="valid-token",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )

    pending_registration_repository.find_by_token.return_value = (
        pending_registration
    )

    created_user = User(
        first_name="smart",
        last_name="kenny",
        email="verify@example.com",
        phone="+2348106086634",
        password="hashed_password",
        role=UserRole.CUSTOMER,
        email_verified=True,
    )

    user_repository.create.return_value = created_user

    result = auth_service.verify_email("valid-token")

    pending_registration_repository.find_by_token.assert_called_once_with(
        "valid-token"
    )

    user_repository.create.assert_called_once()

    pending_registration_repository.delete.assert_called_once_with(
        pending_registration
    )

    assert result == created_user
    assert result.email == "verify@example.com"
    assert result.email_verified is True
    assert result.role == UserRole.CUSTOMER




@pytest.mark.parametrize(
    "email",
    [
        "kennysmart@gmail.com",
        "KENNYSMART@GMAIL.COM",
        " kennysmart@gmail.com ",
        "kEnnySmart@gmail.Com",
    ],
)
def test_register_customer_normalizes_email(auth_service_setup, email):
    auth_service, user_repository, pending_registration_repository = auth_service_setup

    user_repository.find_by_email.return_value = None
    pending_registration_repository.find_by_email.return_value = None
    pending_registration_repository.create.side_effect = (
        lambda registration: registration
    )

    user_data = UserCreate(
        first_name="smart",
        last_name="kenny",
        email=email,
        password="My_Password1234!",
        phone="+2348106086634",
    )

    with patch(
        "app.services.auth_service.EmailService.send_verification_email"
    ):
        registration = auth_service.register_customer(user_data)

    assert registration.email == email.strip().lower()




def test_register_customer_hashes_password(auth_service_setup):
    auth_service, user_repository, pending_registration_repository = auth_service_setup

    user_data = UserCreate(
        first_name="smart",
        last_name="kenny",
        email="kennysmart@gmail.com",
        password="My_Password1234!",
        phone="+2348106086634",
    )

    user_repository.find_by_email.return_value = None
    pending_registration_repository.find_by_email.return_value = None
    pending_registration_repository.create.side_effect = (
        lambda registration: registration
    )

    with patch(
        "app.services.auth_service.EmailService.send_verification_email"
    ):
        registration = auth_service.register_customer(user_data)

    assert registration.password != user_data.password




def test_login_customer_with_correct_password(auth_service_setup):
    auth_service, user_repository, token_repository = auth_service_setup

    user = Mock()
    user.id = "12345678-1234-1234-1234-123456789012"
    user.email = "kennysmart@gmail.com"
    user.password = hash_password("My_Password1234!")
    user.email_verified = True
    user.role = "CUSTOMER"

    user_repository.find_by_email.return_value = user

    with patch(
        "app.services.auth_service.create_access_token",
        return_value="fake-access-token"
    ) as create_token:

        result = auth_service.login(
            email="kennysmart@gmail.com",
            password="My_Password1234!"
        )

    assert result == "fake-access-token"



def test_login_customer_rejects_wrong_password(auth_service_setup):
    auth_service, user_repository, token_repository = auth_service_setup

    user = Mock()
    user.email = "kennysmart@gmail.com"
    user.password = hash_password("My_Password1234!")

    user_repository.find_by_email.return_value = user

    with pytest.raises(AppException, match="Invalid email or password"):
        auth_service.login(
            email="kennysmart@gmail.com",
            password="WrongPassword123!"
        )

    user_repository.find_by_email.assert_called_once_with(
        "kennysmart@gmail.com"
    )



def test_login_customer_rejects_unknown_email(auth_service_setup):
    auth_service, user_repository, token_repository = auth_service_setup

    user_repository.find_by_email.return_value = None

    with pytest.raises(AppException, match="Invalid email or password"):
        auth_service.login(
            email="unknown@gmail.com",
            password="My_Password1234!"
        )

    user_repository.find_by_email.assert_called_once_with(
        "unknown@gmail.com"
    )




@pytest.mark.parametrize(
    "login_email",
    [
        "kennysmart@gmail.com",
        "KENNYSMART@GMAIL.COM",
        " kennysmart@gmail.com ",
        "kEnnySmart@gmail.Com"
    ]
)
def test_login_customer_normalizes_email(auth_service_setup, login_email):
    auth_service, user_repository, token_repository = auth_service_setup

    user = Mock()
    user.id = "12345678-1234-1234-1234-123456789012"
    user.email = "kennysmart@gmail.com"
    user.password = hash_password("My_Password1234!")
    user.email_verified = True
    user.role = "CUSTOMER"

    user_repository.find_by_email.return_value = user

    with patch(
        "app.services.auth_service.create_access_token",
        return_value="fake-access-token"
    ):

        result = auth_service.login(
            email=login_email,
            password="My_Password1234!"
        )

    assert result == "fake-access-token"





def test_login_customer_rejects_unverified_email(auth_service_setup):
    auth_service, user_repository, token_repository = auth_service_setup

    user = Mock()
    user.email = "kennysmart@gmail.com"
    user.password = hash_password("My_Password1234!")
    user.email_verified = False

    user_repository.find_by_email.return_value = user

    with pytest.raises(AppException, match="Email not verified"):
        auth_service.login(
            email="kennysmart@gmail.com",
            password="My_Password1234!"
        )




def test_login_customer_returns_access_token(auth_service_setup):
    auth_service, user_repository, token_repository = auth_service_setup

    user = Mock()
    user.id = "12345678-1234-1234-1234-123456789012"
    user.email = "kennysmart@gmail.com"
    user.password = hash_password("My_Password1234!")
    user.email_verified = True
    user.role = "CUSTOMER"

    user_repository.find_by_email.return_value = user

    with patch(
        "app.services.auth_service.create_access_token",
        return_value="fake-access-token"
    ) as create_token:

        result = auth_service.login(
            email="kennysmart@gmail.com",
            password="My_Password1234!"
        )

    assert result == "fake-access-token"




def test_logout_customer(auth_service_setup):
    auth_service, user_repository, token_repository = auth_service_setup

    user = Mock()
    user.email = "kennysmart@gmail.com"

    user_repository.find_by_email.return_value = user

    result = auth_service.logout("kennysmart@gmail.com")

    assert result is True

    user_repository.find_by_email.assert_called_once_with(
        "kennysmart@gmail.com"
    )



def test_logout_user_not_found(auth_service_setup):
    auth_service, user_repository, token_repository = auth_service_setup

    user_repository.find_by_email.return_value = None

    with pytest.raises(AppException, match="Invalid email or password"):
        auth_service.logout("unknown@gmail.com")

    user_repository.find_by_email.assert_called_once_with(
        "unknown@gmail.com"
    )



@pytest.mark.parametrize(
    "logout_email",
    [
        "kennysmart@gmail.com",
        "KENNYSMART@GMAIL.COM",
        " kennysmart@gmail.com ",
        "kEnnySmart@gmail.Com"
    ]
)
def test_logout_normalizes_email(auth_service_setup, logout_email):
    auth_service, user_repository, token_repository = auth_service_setup

    user = Mock()
    user.email = "kennysmart@gmail.com"

    user_repository.find_by_email.return_value = user

    result = auth_service.logout(logout_email)

    assert result is True

    user_repository.find_by_email.assert_called_once_with(
        "kennysmart@gmail.com"
    )