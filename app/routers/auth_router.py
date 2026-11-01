from fastapi import APIRouter, Depends, Request
from sqlmodel import Session

from app.config.dependencies import get_current_user, get_session
from app.config.security import create_access_token
from app.models.user import User
from app.config.rate_limit import login_limiter
from app.schemas.user_schema import ChangePasswordRequest, ProfileUpdate, TokenResponse, UserProfileResponse, UserCreate, UserResponse, RegistrationResponse, LoginRequest, ForgotPasswordRequest, ResetPasswordRequest
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

@router.get("/verify-email")
def verify_email(
    token: str,
    session: Session = Depends(get_session),
):
    auth_service = AuthService(session)
    auth_service.verify_email(token)

    return {"message": "Email verified successfully. You can now log in."}



@router.post("/forgot-password")
def forgot_password(
    request_data: ForgotPasswordRequest,
    session: Session = Depends(get_session),
):
    AuthService(session).forgot_password(request_data.email)

    return {
        "message": "Password reset instructions have been sent to your email."    }



@router.post("/reset-password")
def reset_password(
    request_data: ResetPasswordRequest,
    session: Session = Depends(get_session),
):
    AuthService(session).reset_password(
        request_data.token,
        request_data.new_password,
    )

    return {
        "message": "Password reset successfully. You can now log in with your new password."
    }


@router.get("/me", response_model=UserProfileResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserProfileResponse)
def update_me(
    changes: ProfileUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return AuthService(session).update_profile(
        current_user, changes.model_dump(exclude_none=True)
    )


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    AuthService(session).change_password(
        current_user, data.current_password, data.new_password
    )
    return {"message": "Password changed successfully."}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(current_user: User = Depends(get_current_user)):
    """Swap a still-valid token for a fresh one (keeps people signed in)."""
    return TokenResponse(
        access_token=create_access_token(current_user.id, current_user.role)
    )
