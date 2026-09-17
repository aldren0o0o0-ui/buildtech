from flask import Request, Response
from app.core import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.modules.auth.schemas import (
    MessageResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.modules.auth.service import (
    authenticate_user,
    clear_refresh_cookie,
    create_user_tokens,
    set_refresh_cookie,
    verify_refresh_token_and_get_user,
)
from app.modules.users.schemas import UserResponse
from app.modules.users.service import create_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account",
)
def register(
    user_in: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Public registration endpoint.
    Strictly creates accounts with CUSTOMER role.
    """
    user = create_user(db=db, user_in=user_in)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in with email and password",
)
def login(
    login_in: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticates user and returns an access token in the response body,
    while setting the refresh token in a secure HttpOnly cookie.
    """
    user = authenticate_user(db=db, email=login_in.email, password=login_in.password)
    access_token, refresh_token = create_user_tokens(user)
    set_refresh_cookie(response, refresh_token)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token using HttpOnly cookie",
)
def refresh_session(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Reads the refresh token from the HttpOnly cookie, validates it,
    and issues a fresh access token and rotated refresh token cookie.
    """
    refresh_token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cookie missing.",
        )

    user = verify_refresh_token_and_get_user(db=db, refresh_token=refresh_token)
    new_access_token, new_refresh_token = create_user_tokens(user)
    set_refresh_cookie(response, new_refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Log out and expire refresh cookie",
)
def logout(response: Response):
    """
    Expires and clears the refresh token cookie.
    """
    clear_refresh_cookie(response)
    return MessageResponse(message="Successfully logged out.")
