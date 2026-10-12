from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlmodel import Session

from app.config.database import engine
from app.config.security import decode_access_token
from app.enums.user_role import UserRole
from app.exceptions.app_exception import AppException
from app.models.user import User
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_session():
    with Session(engine) as session:
        yield session


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise AppException("Not authenticated", status_code=401)

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise AppException("Invalid or expired token", status_code=401)

    user = UserRepository(session).find_by_id(user_id)

    if user is None or not user.email_verified:
        raise AppException("Invalid or expired token", status_code=401)

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.WORKSHOP_ADMIN:
        raise AppException("Admin access required", status_code=403)
    return user