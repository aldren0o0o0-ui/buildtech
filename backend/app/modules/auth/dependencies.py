from typing import Optional
from app.core import Depends, HTTPException, status
from app.core import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.modules.users.models import User, UserRole
from app.modules.users.service import get_user_by_id

security = HTTPBearer(auto_error=False)


def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that extracts the Bearer token, validates it, and resolves
    the active user from the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not auth_header or not auth_header.credentials:
        raise credentials_exception

    token = auth_header.credentials
    payload = decode_token(token)
    if not payload:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = get_user_by_id(db, user_id)
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_optional_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Optional authentication dependency.
    Returns the User if a valid access token is present; otherwise returns None.
    """
    if not auth_header or not auth_header.credentials:
        return None

    try:
        payload = decode_token(auth_header.credentials)
        if not payload or payload.get("type") != "access":
            return None

        user_id_str = payload.get("sub")
        if not user_id_str:
            return None

        user_id = int(user_id_str)
        user = get_user_by_id(db, user_id)
        if user and user.is_active:
            return user
        return None
    except Exception:
        return None


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that ensures the authenticated user has the ADMIN role.
    Returns 403 Forbidden if the user is a CUSTOMER or has another role.
    """
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin privileges required.",
        )
    return current_user


def require_customer(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that ensures the authenticated user has the CUSTOMER role.
    Returns 403 Forbidden if the user is an ADMIN or has another role.
    """
    if current_user.role != UserRole.CUSTOMER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Customer privileges required.",
        )
    return current_user

