import pytest
from app.core.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.db.models import Base  # Explicit model registry
from app.db.session import get_db
from app.main import app
from app.modules.users.models import User, UserRole

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database tables for each test function."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Flask TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_customer_user(db_session):
    """Creates a regular CUSTOMER user in the test database."""
    user = User(
        email="customer@example.com",
        password_hash=hash_password("Password123!"),
        first_name="Jane",
        last_name="Doe",
        role=UserRole.CUSTOMER.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin_user(db_session):
    """Creates an ADMIN user in the test database."""
    user = User(
        email="admin@example.com",
        password_hash=hash_password("AdminPass123!"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_inactive_user(db_session):
    """Creates an inactive user in the test database."""
    user = User(
        email="inactive@example.com",
        password_hash=hash_password("InactivePass123!"),
        first_name="Inactive",
        last_name="User",
        role=UserRole.CUSTOMER.value,
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def customer_auth_headers(test_customer_user):
    """Returns Bearer authorization headers for the test customer."""
    token = create_access_token(
        subject=test_customer_user.id,
        role=test_customer_user.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(test_admin_user):
    """Returns Bearer authorization headers for the test admin."""
    token = create_access_token(
        subject=test_admin_user.id,
        role=test_admin_user.role,
    )
    return {"Authorization": f"Bearer {token}"}
