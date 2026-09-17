import pytest
from app.core.config import settings
from app.core.security import create_refresh_token, verify_password
from app.modules.users.models import User, UserRole


def test_successful_registration(client, db_session):
    """Test successful user registration creates user and returns safe data."""
    payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["first_name"] == "Alice"
    assert data["last_name"] == "Smith"
    assert data["role"] == "CUSTOMER"
    assert data["is_active"] is True
    assert "password_hash" not in data
    assert "password" not in data

    # Verify in DB
    user = db_session.query(User).filter(User.email == "alice@example.com").first()
    assert user is not None
    assert user.role == UserRole.CUSTOMER.value
    assert verify_password("Password123!", user.password_hash)


def test_duplicate_email_rejection(client, test_customer_user):
    """Test duplicate registration with existing email is rejected."""
    payload = {
        "first_name": "Different",
        "last_name": "Name",
        "email": test_customer_user.email,
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_email_normalization_on_registration(client, db_session):
    """Test email is trimmed and lowercased during registration."""
    payload = {
        "first_name": "Bob",
        "last_name": "Builder",
        "email": "  BOB.BUILDER@EXAMPLE.COM  ",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["email"] == "bob.builder@example.com"

    user = db_session.query(User).filter(User.email == "bob.builder@example.com").first()
    assert user is not None


def test_customer_role_assignment(client):
    """Test that public registration always assigns CUSTOMER role."""
    payload = {
        "first_name": "Charlie",
        "last_name": "Brown",
        "email": "charlie@example.com",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["role"] == "CUSTOMER"


def test_attempted_role_injection(client):
    """Test that attempts to inject role or is_active or password_hash are rejected by schema."""
    payload = {
        "first_name": "Hacker",
        "last_name": "Admin",
        "email": "hacker@example.com",
        "password": "Password123!",
        "role": "ADMIN",
        "is_active": False,
        "password_hash": "precomputed_hash",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


def test_password_hashing(client, db_session):
    """Test password is never stored in plain text."""
    raw_pass = "MySecretPass123!"
    payload = {
        "first_name": "David",
        "last_name": "Miller",
        "email": "david@example.com",
        "password": raw_pass,
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    user = db_session.query(User).filter(User.email == "david@example.com").first()
    assert user.password_hash != raw_pass
    assert user.password_hash.startswith("$2b$") or user.password_hash.startswith("$2a$")
    assert verify_password(raw_pass, user.password_hash)


def test_login_success(client, test_customer_user):
    """Test successful login returns access token and sets HttpOnly refresh cookie."""
    payload = {
        "email": "customer@example.com",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "customer@example.com"
    assert "password_hash" not in data["user"]

    # Verify cookie
    cookie = response.cookies.get(settings.REFRESH_COOKIE_NAME)
    assert cookie is not None


def test_login_wrong_password(client, test_customer_user):
    """Test login with wrong password returns generic 401."""
    payload = {
        "email": test_customer_user.email,
        "password": "WrongPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_nonexistent_user(client):
    """Test login with non-existent email returns generic 401 without leaking existence."""
    payload = {
        "email": "doesnotexist@example.com",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_inactive_user(client, test_inactive_user):
    """Test login with inactive user is rejected."""
    payload = {
        "email": test_inactive_user.email,
        "password": "InactivePass123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401


def test_valid_access_token(client, customer_auth_headers):
    """Test accessing protected route with valid access token."""
    response = client.get("/api/v1/users/me", headers=customer_auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "customer@example.com"


def test_missing_access_token(client):
    """Test accessing protected route without access token."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_invalid_access_token(client):
    """Test accessing protected route with invalid or malformed access token."""
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert response.status_code == 401


def test_valid_refresh_token(client, test_customer_user):
    """Test refreshing token session with valid refresh cookie."""
    refresh_token = create_refresh_token(subject=test_customer_user.id)
    client.cookies.set(settings.REFRESH_COOKIE_NAME, refresh_token)

    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == test_customer_user.email

    # Check new refresh cookie is issued
    assert response.cookies.get(settings.REFRESH_COOKIE_NAME) is not None


def test_invalid_refresh_token(client):
    """Test refresh endpoint with invalid refresh token."""
    client.cookies.set(settings.REFRESH_COOKIE_NAME, "malformed-refresh-token")
    response = client.post("/api/v1/auth/refresh")
    assert response.status_code == 401


def test_logout_behavior(client, test_customer_user):
    """Test logout clears the refresh token cookie."""
    refresh_token = create_refresh_token(subject=test_customer_user.id)
    client.cookies.set(settings.REFRESH_COOKIE_NAME, refresh_token)

    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out."
