from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.config.dependencies import get_session
from app.schemas.user_schema import UserCreate, UserResponse, RegistrationResponse
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth")


@router.post("/register", response_model=RegistrationResponse)
def register_customer(
    user_data: UserCreate,
    session: Session = Depends(get_session),
):
    auth_service = AuthService(session)

    auth_service.register_customer(user_data)

    return {
        "message": "Please check your email to verify your account."
    }


@router.get("/verify-email", response_model=UserResponse)
def verify_email(
    token: str,
    session: Session = Depends(get_session),
):
    auth_service = AuthService(session)
    return auth_service.verify_email(token)