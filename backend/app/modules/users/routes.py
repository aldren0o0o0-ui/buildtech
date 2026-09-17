from app.core import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.schemas import MessageResponse
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.users.models import User
from app.modules.users.schemas import (
    ChangePasswordRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.modules.users.service import change_user_password, update_user_profile

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the authenticated user's profile details.
    """
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update basic profile details",
)
def update_me(
    update_in: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates the authenticated user's first_name and last_name.
    """
    updated_user = update_user_profile(
        db=db,
        user=current_user,
        update_in=update_in,
    )
    return updated_user


@router.post(
    "/me/change-password",
    response_model=MessageResponse,
    summary="Change user password",
)
def change_password(
    password_in: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verifies current password and updates to new password.
    """
    change_user_password(
        db=db,
        user=current_user,
        password_in=password_in,
    )
    return MessageResponse(message="Password changed successfully.")


@router.get(
    "/admin-check",
    response_model=MessageResponse,
    summary="Verify admin authorization",
)
def admin_check(admin_user: User = Depends(require_admin)):
    """
    Admin-only endpoint for verifying role authorization.
    """
    return MessageResponse(message=f"Admin authorization confirmed for {admin_user.email}.")
