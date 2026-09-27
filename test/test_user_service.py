import pytest
from unittest.mock import Mock

from app.services.user_service import UserService


def test_get_user_by_id_returns_user():
    session = Mock()
    user_repository = Mock()

    user_service = UserService(session)
    user_service.user_repository = user_repository

    user = Mock()
    user.id = "12345678-1234-1234-1234-123456789012"

    user_repository.find_by_id.return_value = user

    result = user_service.get_user_by_id(user.id)

    assert result == user

    user_repository.find_by_id.assert_called_once_with(user.id)



def test_get_user_by_id_returns_none_when_user_not_found():
    session = Mock()
    user_repository = Mock()

    user_service = UserService(session)
    user_service.user_repository = user_repository

    user_repository.find_by_id.return_value = None

    user_id = "12345678-1234-1234-1234-123456789012"

    result = user_service.get_user_by_id(user_id)

    assert result is None

    user_repository.find_by_id.assert_called_once_with(user_id)




def test_get_user_by_email_returns_user():
    session = Mock()
    user_repository = Mock()

    user_service = UserService(session)
    user_service.user_repository = user_repository

    user = Mock()
    user.email = "kennysmart@gmail.com"

    user_repository.find_by_email.return_value = user

    result = user_service.get_user_by_email("kennysmart@gmail.com")

    assert result == user

    user_repository.find_by_email.assert_called_once_with(
        "kennysmart@gmail.com"
    )



def test_get_user_by_email_returns_none_when_user_not_found():
    session = Mock()
    user_repository = Mock()

    user_service = UserService(session)
    user_service.user_repository = user_repository

    user_repository.find_by_email.return_value = None

    email = "unknown@gmail.com"

    result = user_service.get_user_by_email(email)

    assert result is None

    user_repository.find_by_email.assert_called_once_with(email)




def test_create_user_returns_created_user():
    session = Mock()
    user_repository = Mock()

    user_service = UserService(session)
    user_service.user_repository = user_repository

    user = Mock()

    user_repository.create.return_value = user

    result = user_service.create_user(user)

    assert result == user

    user_repository.create.assert_called_once_with(user)