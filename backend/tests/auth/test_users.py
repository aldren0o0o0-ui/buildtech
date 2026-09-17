import pytest
from app.core.security import verify_password
from app.modules.users.models import User


def test_get_current_user_me(client, customer_auth_headers, test_customer_user):
    """Test GET /api/v1/users/me returns authenticated user's profile."""
    response = client.get("/api/v1/users/me", headers=customer_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_customer_user.id
    assert data["email"] == "customer@example.com"
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Doe"
    assert data["role"] == "CUSTOMER"
    assert "password_hash" not in data


def test_update_user_profile(client, customer_auth_headers, db_session, test_customer_user):
    """Test PATCH /api/v1/users/me updates first_name and last_name."""
    update_payload = {
        "first_name": "Janet",
        "last_name": "Jackson",
    }
    response = client.patch(
        "/api/v1/users/me",
        json=update_payload,
        headers=customer_auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Janet"
    assert data["last_name"] == "Jackson"

    # Verify in DB
    user = db_session.query(User).filter(User.id == test_customer_user.id).first()
    assert user.first_name == "Janet"
    assert user.last_name == "Jackson"


def test_change_password_success(client, customer_auth_headers, db_session, test_customer_user):
    """Test successful password change with valid current password."""
    payload = {
        "current_password": "Password123!",
        "new_password": "NewBrandPassword456!",
    }
    response = client.post(
        "/api/v1/users/me/change-password",
        json=payload,
        headers=customer_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully."

    # Verify password has changed in DB
    db_session.refresh(test_customer_user)
    assert verify_password("NewBrandPassword456!", test_customer_user.password_hash)
    assert not verify_password("Password123!", test_customer_user.password_hash)


def test_change_password_wrong_current(client, customer_auth_headers, test_customer_user):
    """Test password change fails when current password is wrong."""
    payload = {
        "current_password": "WrongCurrentPassword123!",
        "new_password": "NewBrandPassword456!",
    }
    response = client.post(
        "/api/v1/users/me/change-password",
        json=payload,
        headers=customer_auth_headers,
    )
    assert response.status_code == 400
    assert "Current password is incorrect" in response.json()["detail"]


def test_customer_denied_admin_access(client, customer_auth_headers):
    """Test customer user receives 403 Forbidden on admin-protected endpoint."""
    response = client.get("/api/v1/users/admin-check", headers=customer_auth_headers)
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]


def test_admin_allowed_admin_access(client, admin_auth_headers):
    """Test admin user receives 200 OK on admin-protected endpoint."""
    response = client.get("/api/v1/users/admin-check", headers=admin_auth_headers)
    assert response.status_code == 200
    assert "Admin authorization confirmed" in response.json()["message"]
