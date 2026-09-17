from typing import TYPE_CHECKING, Optional
from app.core import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.modules.users.models import User, UserRole
from app.modules.users.schemas import ChangePasswordRequest, UserUpdateRequest

if TYPE_CHECKING:
    from app.modules.auth.schemas import UserRegisterRequest


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Retrieve user by database ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieve user by normalized email."""
    normalized_email = email.strip().lower()
    return db.query(User).filter(User.email == normalized_email).first()


def create_user(
    db: Session,
    user_in: "UserRegisterRequest",
    role: str = UserRole.CUSTOMER.value,
) -> User:
    """
    Creates a new user in the database.
    Public registration strictly assigns the CUSTOMER role.
    """
    normalized_email = user_in.email.strip().lower()
    existing_user = get_user_by_email(db, normalized_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )

    # Ensure role is strictly valid (CUSTOMER for public registration)
    assigned_role = UserRole.CUSTOMER.value if role != UserRole.ADMIN.value else role

    db_user = User(
        email=normalized_email,
        password_hash=hash_password(user_in.password),
        first_name=user_in.first_name.strip(),
        last_name=user_in.last_name.strip(),
        role=assigned_role,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_profile(
    db: Session,
    user: User,
    update_in: UserUpdateRequest,
) -> User:
    """Updates the first_name and last_name of the user."""
    if update_in.first_name is not None:
        user.first_name = update_in.first_name.strip()
    if update_in.last_name is not None:
        user.last_name = update_in.last_name.strip()

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def change_user_password(
    db: Session,
    user: User,
    password_in: ChangePasswordRequest,
) -> None:
    """
    Verifies current password and updates to the new hashed password.
    """
    if not verify_password(password_in.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    user.password_hash = hash_password(password_in.new_password)
    db.add(user)
    db.commit()
