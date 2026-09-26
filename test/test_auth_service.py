import pytest
from unittest.mock import Mock

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