import pytest
from app.core.security import create_access_token, hash_password
from app.modules.addresses.models import Address
from app.modules.users.models import User, UserRole


@pytest.fixture
def second_customer_user(db_session):
    user = User(
        email="customer2@example.com",
        password_hash=hash_password("Customer123!"),
        first_name="Customer",
        last_name="Two",
        role=UserRole.CUSTOMER.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_customer_auth_headers(second_customer_user):
    token = create_access_token(
        subject=second_customer_user.id,
        role=second_customer_user.role,
    )
    return {"Authorization": f"Bearer {token}"}


# =========================================================================
# 1. Address Creation & Default Rules
# =========================================================================

def test_create_address_first_becomes_default(client, customer_auth_headers):
    """The customer's first saved address automatically becomes default."""
    payload = {
        "label": "Home",
        "recipient_name": "Juan Dela Cruz",
        "phone": "09171234567",
        "address_line1": "123 Rizal Ave",
        "barangay": "Barangay 1",
        "city": "Manila",
        "province": "Metro Manila",
        "postal_code": "1000",
        "country": "Philippines",
        "is_default": False,  # Even if False, first address becomes default
    }
    res = client.post("/api/v1/addresses", json=payload, headers=customer_auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["is_default"] is True
    assert data["recipient_name"] == "Juan Dela Cruz"
    assert data["label"] == "Home"


def test_create_second_address_defaults_to_false(client, customer_auth_headers):
    """A second address does not become default unless explicitly specified."""
    p1 = {
        "recipient_name": "Juan Dela Cruz",
        "phone": "09171234567",
        "address_line1": "123 Rizal Ave",
        "barangay": "Barangay 1",
        "city": "Manila",
        "province": "Metro Manila",
        "postal_code": "1000",
    }
    client.post("/api/v1/addresses", json=p1, headers=customer_auth_headers)

    p2 = {
        "label": "Office",
        "recipient_name": "Juan Dela Cruz",
        "phone": "09179876543",
        "address_line1": "456 Ayala Ave",
        "barangay": "San Lorenzo",
        "city": "Makati",
        "province": "Metro Manila",
        "postal_code": "1223",
        "is_default": False,
    }
    res2 = client.post("/api/v1/addresses", json=p2, headers=customer_auth_headers)
    assert res2.status_code == 201
    assert res2.json()["is_default"] is False


def test_create_address_with_is_default_true_unsets_previous_default(
    client, customer_auth_headers, db_session, test_customer_user
):
    """Creating an address with is_default=True atomically unsets the previous default."""
    p1 = {
        "recipient_name": "Juan Dela Cruz",
        "phone": "09171234567",
        "address_line1": "123 Rizal Ave",
        "barangay": "Barangay 1",
        "city": "Manila",
        "province": "Metro Manila",
        "postal_code": "1000",
    }
    r1 = client.post("/api/v1/addresses", json=p1, headers=customer_auth_headers)
    id1 = r1.json()["id"]

    p2 = {
        "recipient_name": "Juan Dela Cruz",
        "phone": "09179876543",
        "address_line1": "456 Ayala Ave",
        "barangay": "San Lorenzo",
        "city": "Makati",
        "province": "Metro Manila",
        "postal_code": "1223",
        "is_default": True,
    }
    r2 = client.post("/api/v1/addresses", json=p2, headers=customer_auth_headers)
    id2 = r2.json()["id"]
    assert r2.json()["is_default"] is True

    # Check database: address 1 is no longer default, address 2 is default
    a1 = db_session.query(Address).filter(Address.id == id1).first()
    a2 = db_session.query(Address).filter(Address.id == id2).first()
    assert a1.is_default is False
    assert a2.is_default is True


# =========================================================================
# 2. Listing & Retrieving Addresses
# =========================================================================

def test_list_addresses_ordered_with_default_first(client, customer_auth_headers):
    """Listing customer addresses returns default address first."""
    p1 = {
        "recipient_name": "Juan Dela Cruz",
        "phone": "09171234567",
        "address_line1": "123 Rizal Ave",
        "barangay": "Barangay 1",
        "city": "Manila",
        "province": "Metro Manila",
        "postal_code": "1000",
    }
    client.post("/api/v1/addresses", json=p1, headers=customer_auth_headers)

    p2 = {
        "label": "Office",
        "recipient_name": "Juan Dela Cruz",
        "phone": "09179876543",
        "address_line1": "456 Ayala Ave",
        "barangay": "San Lorenzo",
        "city": "Makati",
        "province": "Metro Manila",
        "postal_code": "1223",
        "is_default": True,
    }
    client.post("/api/v1/addresses", json=p2, headers=customer_auth_headers)

    res = client.get("/api/v1/addresses", headers=customer_auth_headers)
    assert res.status_code == 200
    addresses = res.json()
    assert len(addresses) == 2
    assert addresses[0]["is_default"] is True
    assert addresses[0]["label"] == "Office"
    assert addresses[1]["is_default"] is False


def test_get_address_by_id_success(client, customer_auth_headers):
    """Customer can fetch their own address by ID."""
    p1 = {
        "recipient_name": "Juan Dela Cruz",
        "phone": "09171234567",
        "address_line1": "123 Rizal Ave",
        "barangay": "Barangay 1",
        "city": "Manila",
        "province": "Metro Manila",
        "postal_code": "1000",
    }
    created = client.post("/api/v1/addresses", json=p1, headers=customer_auth_headers).json()
    addr_id = created["id"]

    res = client.get(f"/api/v1/addresses/{addr_id}", headers=customer_auth_headers)
    assert res.status_code == 200
    assert res.json()["id"] == addr_id
    assert res.json()["city"] == "Manila"


def test_get_address_customer_isolation(client, customer_auth_headers, second_customer_auth_headers):
    """Customer B cannot view Customer A's address and receives 404 Not Found."""
    p1 = {
        "recipient_name": "Juan Dela Cruz",
        "phone": "09171234567",
        "address_line1": "123 Rizal Ave",
        "barangay": "Barangay 1",
        "city": "Manila",
        "province": "Metro Manila",
        "postal_code": "1000",
    }
    created = client.post("/api/v1/addresses", json=p1, headers=customer_auth_headers).json()
    addr_id = created["id"]

    res = client.get(f"/api/v1/addresses/{addr_id}", headers=second_customer_auth_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


# =========================================================================
# 3. Updating Addresses
# =========================================================================

def test_update_address_fields_success(client, customer_auth_headers):
    """Updating address properties persists changes."""
    p1 = {
        "recipient_name": "Juan Dela Cruz",
        "phone": "09171234567",
        "address_line1": "123 Old St",
        "barangay": "Barangay 1",
        "city": "Manila",
        "province": "Metro Manila",
        "postal_code": "1000",
    }
    created = client.post("/api/v1/addresses", json=p1, headers=customer_auth_headers).json()
    addr_id = created["id"]

    update_payload = {
        "recipient_name": "Juan M. Dela Cruz",
        "address_line1": "789 New St",
    }
    res = client.patch(f"/api/v1/addresses/{addr_id}", json=update_payload, headers=customer_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["recipient_name"] == "Juan M. Dela Cruz"
    assert data["address_line1"] == "789 New St"
    assert data["city"] == "Manila"


def test_update_address_set_default_unsets_previous_default(
    client, customer_auth_headers, db_session
):
    """Updating an address to is_default=True atomically unsets previous default."""
    r1 = client.post(
        "/api/v1/addresses",
        json={
            "recipient_name": "Juan",
            "phone": "09171234567",
            "address_line1": "123 Street A",
            "barangay": "B1",
            "city": "C1",
            "province": "P1",
            "postal_code": "1000",
        },
        headers=customer_auth_headers,
    )
    id1 = r1.json()["id"]

    r2 = client.post(
        "/api/v1/addresses",
        json={
            "recipient_name": "Juan",
            "phone": "09171234567",
            "address_line1": "456 Street B",
            "barangay": "B2",
            "city": "C2",
            "province": "P2",
            "postal_code": "1000",
        },
        headers=customer_auth_headers,
    )
    id2 = r2.json()["id"]
    assert r1.json()["is_default"] is True
    assert r2.json()["is_default"] is False

    # Update address 2 to default
    client.patch(f"/api/v1/addresses/{id2}", json={"is_default": True}, headers=customer_auth_headers)

    a1 = db_session.query(Address).filter(Address.id == id1).first()
    a2 = db_session.query(Address).filter(Address.id == id2).first()
    assert a1.is_default is False
    assert a2.is_default is True


# =========================================================================
# 4. Deleting Addresses & Promotion of Default
# =========================================================================

def test_delete_non_default_address(client, customer_auth_headers, db_session):
    """Deleting a non-default address succeeds and leaves the default address untouched."""
    r1 = client.post(
        "/api/v1/addresses",
        json={
            "recipient_name": "Juan",
            "phone": "09171234567",
            "address_line1": "123 Street A",
            "barangay": "B1",
            "city": "C1",
            "province": "P1",
            "postal_code": "1000",
        },
        headers=customer_auth_headers,
    )
    id1 = r1.json()["id"]

    r2 = client.post(
        "/api/v1/addresses",
        json={
            "recipient_name": "Juan",
            "phone": "09171234567",
            "address_line1": "456 Street B",
            "barangay": "B2",
            "city": "C2",
            "province": "P2",
            "postal_code": "1000",
        },
        headers=customer_auth_headers,
    )
    id2 = r2.json()["id"]

    del_res = client.delete(f"/api/v1/addresses/{id2}", headers=customer_auth_headers)
    assert del_res.status_code == 200

    a1 = db_session.query(Address).filter(Address.id == id1).first()
    a2 = db_session.query(Address).filter(Address.id == id2).first()
    assert a1.is_default is True
    assert a2 is None


def test_delete_default_address_promotes_remaining_address(
    client, customer_auth_headers, db_session
):
    """Deleting the default address automatically promotes the next remaining address to default."""
    r1 = client.post(
        "/api/v1/addresses",
        json={
            "recipient_name": "Juan",
            "phone": "09171234567",
            "address_line1": "123 Street A",
            "barangay": "B1",
            "city": "C1",
            "province": "P1",
            "postal_code": "1000",
        },
        headers=customer_auth_headers,
    )
    id1 = r1.json()["id"]

    r2 = client.post(
        "/api/v1/addresses",
        json={
            "recipient_name": "Juan",
            "phone": "09171234567",
            "address_line1": "456 Street B",
            "barangay": "B2",
            "city": "C2",
            "province": "P2",
            "postal_code": "1000",
        },
        headers=customer_auth_headers,
    )
    id2 = r2.json()["id"]

    # id1 was default. Delete it.
    del_res = client.delete(f"/api/v1/addresses/{id1}", headers=customer_auth_headers)
    assert del_res.status_code == 200

    a2 = db_session.query(Address).filter(Address.id == id2).first()
    assert a2 is not None
    assert a2.is_default is True


def test_customer_cannot_delete_other_customer_address(
    client, customer_auth_headers, second_customer_auth_headers
):
    """Customer B receives 404 when attempting to delete Customer A's address."""
    r1 = client.post(
        "/api/v1/addresses",
        json={
            "recipient_name": "Juan",
            "phone": "09171234567",
            "address_line1": "123 Street A",
            "barangay": "B1",
            "city": "C1",
            "province": "P1",
            "postal_code": "1000",
        },
        headers=customer_auth_headers,
    )
    id1 = r1.json()["id"]

    res = client.delete(f"/api/v1/addresses/{id1}", headers=second_customer_auth_headers)
    assert res.status_code == 404


def test_explicit_set_default_address_endpoint(client, customer_auth_headers, db_session):
    """Calling POST /{address_id}/default explicitly marks the address as default."""
    r1 = client.post(
        "/api/v1/addresses",
        json={
            "recipient_name": "Juan",
            "phone": "09171234567",
            "address_line1": "123 Street A",
            "barangay": "B1",
            "city": "C1",
            "province": "P1",
            "postal_code": "1000",
        },
        headers=customer_auth_headers,
    )
    id1 = r1.json()["id"]

    r2 = client.post(
        "/api/v1/addresses",
        json={
            "recipient_name": "Juan",
            "phone": "09171234567",
            "address_line1": "456 Street B",
            "barangay": "B2",
            "city": "C2",
            "province": "P2",
            "postal_code": "1000",
        },
        headers=customer_auth_headers,
    )
    id2 = r2.json()["id"]

    res = client.post(f"/api/v1/addresses/{id2}/default", headers=customer_auth_headers)
    assert res.status_code == 200
    assert res.json()["is_default"] is True

    a1 = db_session.query(Address).filter(Address.id == id1).first()
    a2 = db_session.query(Address).filter(Address.id == id2).first()
    assert a1.is_default is False
    assert a2.is_default is True


# =========================================================================
# 5. Security & Authorization
# =========================================================================

def test_unauthenticated_address_access_rejected(client):
    """Unauthenticated requests are rejected with 401 Unauthorized."""
    assert client.get("/api/v1/addresses").status_code == 401
    assert client.post("/api/v1/addresses", json={}).status_code == 401
    assert client.get("/api/v1/addresses/1").status_code == 401
    assert client.delete("/api/v1/addresses/1").status_code == 401


def test_admin_address_access_rejected(client, admin_auth_headers):
    """Admin users receive 403 Forbidden on customer address endpoints."""
    assert client.get("/api/v1/addresses", headers=admin_auth_headers).status_code == 403
    assert client.post("/api/v1/addresses", json={}, headers=admin_auth_headers).status_code == 403


def test_create_address_validation_rejects_empty_or_whitespace(client, customer_auth_headers):
    """Validation rejects empty or whitespace-only required fields."""
    invalid_payload = {
        "recipient_name": "   ",
        "phone": "09171234567",
        "address_line1": "123 Main St",
        "barangay": "Barangay 1",
        "city": "Manila",
        "province": "Metro Manila",
        "postal_code": "1000",
    }
    res = client.post("/api/v1/addresses", json=invalid_payload, headers=customer_auth_headers)
    assert res.status_code == 422


def test_user_deletion_cascades_to_addresses(client, customer_auth_headers, test_customer_user, db_session):
    """Deleting a user cascades and removes all their addresses."""
    client.post(
        "/api/v1/addresses",
        json={
            "recipient_name": "Juan",
            "phone": "09171234567",
            "address_line1": "123 Street A",
            "barangay": "B1",
            "city": "C1",
            "province": "P1",
            "postal_code": "1000",
        },
        headers=customer_auth_headers,
    )
    assert db_session.query(Address).filter(Address.user_id == test_customer_user.id).count() == 1

    db_session.delete(test_customer_user)
    db_session.commit()

    assert db_session.query(Address).filter(Address.user_id == test_customer_user.id).count() == 0

