from urllib.request import Request

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.config.dependencies import get_session
from app.config.rate_limit import login_limiter
from app.schemas.user_schema import UserCreate, UserResponse, RegistrationResponse, LoginRequest
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



@router.post("/login")
def login(
    request: Request,
    login_data: LoginRequest,
    session: Session = Depends(get_session),
):
    key = f"{request.client.host}:{login_data.email.lower()}"
    login_limiter.check(key)

    token = AuthService(session).login(login_data.email, login_data.password)

    login_limiter.reset(key)  # a successful login clears the counter
    return {"access_token": token, "token_type": "bearer"}

@router.post("/logout")
def logout(email: str,
           session: Session = Depends(get_session)
           ):

    auth_service = AuthService(session)
    auth_service.logout(email)
    return {
        "message": "Logged out successfully.",
    }



@router.get("/verify-email")
def verify_email(
    token: str,
    session: Session = Depends(get_session),
):
    auth_service = AuthService(session)
    auth_service.verify_email(token)

    return {"message": "Email verified successfully. You can now log in."}