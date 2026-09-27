import pytest
from unittest.mock import Mock, patch

from app.config.password import hash_password
from app.exceptions.app_exception import AppException
from app.schemas.user_schema import UserCreate
from app.services.auth_service import AuthService


@pytest.fixture
def auth_service_setup():
    session = Mock()
    user_repository = Mock()
    token_repository = Mock()

    auth_service = AuthService(session)

    auth_service.user_repository = user_repository
    auth_service.token_repository = token_repository

    return auth_service, user_repository, token_repository


def test_register_create_customer(auth_service_setup):
    auth_service, user_repository, token_repository = auth_service_setup

    user_data = UserCreate(
        first_name="smart",
        last_name="kenny",
        email="kennysmart@gmail.com",
        password="My_Password1234!",
        phone="+2348106086634"
    )

    user_repository.find_by_email.return_value = None
    user_repository.create.side_effect = lambda user: user

    create_user = auth_service.register_customer(user_data)

    user_repository.find_by_email.assert_called_once_with("kennysmart@gmail.com")

    user_repository.create.assert_called_once()

    assert create_user is not None
    assert create_user.first_name == "smart"
    assert create_user.last_name == "kenny"
    assert create_user.email == "kennysmart@gmail.com"
    assert create_user.phone == "+2348106086634"
    assert create_user.role.value == "CUSTOMER"


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



@pytest.mark.parametrize(
    "email",
    ["kennysmart@gmail.com", "KENNYSMART@GMAIL.COM", " kennysmart@gmail.com ", "kEnnySmart@gmail.Com"])
def test_register_customer_normalizes_email(auth_service_setup, email):
    auth_service, user_repository, token_repository = auth_service_setup

    user_repository.find_by_email.return_value = None
    user_repository.create.side_effect = lambda user: user

    user_data = UserCreate(
        first_name="smart",
        last_name="kenny",
        email=email,
        password="My_Password1234!",
        phone="+2348106086634"
    )

    create_user = auth_service.register_customer(user_data)

    assert create_user.email == email.strip().lower()




def test_register_customer_hashes_password(auth_service_setup):
    auth_service, user_repository, token_repository = auth_service_setup

    user_data = UserCreate(
        first_name="smart",
        last_name="kenny",
        email="kennysmart@gmail.com",
        password="My_Password1234!",
        phone="+2348106086634"
    )

    user_repository.find_by_email.return_value = None
    user_repository.create.side_effect = lambda user: user

    create_user = auth_service.register_customer(user_data)

    assert create_user.password != user_data.password


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