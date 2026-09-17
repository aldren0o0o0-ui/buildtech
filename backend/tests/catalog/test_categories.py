import pytest
from app.modules.catalog.category_model import Category


def test_public_list_active_categories(client, db_session):
    """Test public listing returns only active categories."""
    cat1 = Category(name="Processors", slug="processors", is_active=True)
    cat2 = Category(name="Graphics Cards", slug="graphics-cards", is_active=True)
    cat3 = Category(name="Legacy Parts", slug="legacy-parts", is_active=False)
    db_session.add_all([cat1, cat2, cat3])
    db_session.commit()

    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.json()
    slugs = [c["slug"] for c in data]
    assert "graphics-cards" in slugs
    assert "processors" in slugs
    assert "legacy-parts" not in slugs


def test_get_category_by_id(client, db_session):
    """Test retrieving a single active category by ID."""
    cat = Category(name="Memory", slug="memory", description="DDR4 and DDR5 RAM", is_active=True)
    db_session.add(cat)
    db_session.commit()

    response = client.get(f"/api/v1/categories/{cat.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == cat.id
    assert data["name"] == "Memory"
    assert data["slug"] == "memory"
    assert data["description"] == "DDR4 and DDR5 RAM"


def test_create_category_as_admin(client, admin_auth_headers, db_session):
    """Test creating a category as an authenticated ADMIN."""
    payload = {
        "name": "Solid State Drives",
        "description": "NVMe and SATA SSDs",
        "is_active": True,
    }
    response = client.post("/api/v1/categories", json=payload, headers=admin_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Solid State Drives"
    assert data["slug"] == "solid-state-drives"
    assert data["is_active"] is True

    # Verify in DB
    db_cat = db_session.query(Category).filter(Category.slug == "solid-state-drives").first()
    assert db_cat is not None


def test_customer_cannot_create_category(client, customer_auth_headers):
    """Test that a CUSTOMER user receives 403 when attempting to create a category."""
    payload = {"name": "Power Supplies"}
    response = client.post("/api/v1/categories", json=payload, headers=customer_auth_headers)
    assert response.status_code == 403


def test_unauthenticated_cannot_create_category(client):
    """Test that unauthenticated request receives 401 when attempting to create a category."""
    payload = {"name": "Motherboards"}
    response = client.post("/api/v1/categories", json=payload)
    assert response.status_code == 401


def test_duplicate_category_name_rejected(client, admin_auth_headers, db_session):
    """Test that creating a category with an existing name is rejected."""
    cat = Category(name="Cooling", slug="cooling", is_active=True)
    db_session.add(cat)
    db_session.commit()

    payload = {"name": "  COOLING  "}
    response = client.post("/api/v1/categories", json=payload, headers=admin_auth_headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_slug_generated_deterministically(client, admin_auth_headers):
    """Test slug is cleaned, lowercased, and hyphens applied."""
    payload = {"name": "  Custom Liquid Cooling & Accessories!  "}
    response = client.post("/api/v1/categories", json=payload, headers=admin_auth_headers)
    assert response.status_code == 201
    assert response.json()["slug"] == "custom-liquid-cooling-accessories"


def test_update_category(client, admin_auth_headers, db_session):
    """Test updating a category's name and description."""
    cat = Category(name="Monitors", slug="monitors", is_active=True)
    db_session.add(cat)
    db_session.commit()

    payload = {
        "name": "Gaming Displays",
        "description": "High refresh-rate gaming monitors",
    }
    response = client.patch(f"/api/v1/categories/{cat.id}", json=payload, headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Gaming Displays"
    assert data["slug"] == "gaming-displays"
    assert data["description"] == "High refresh-rate gaming monitors"


def test_deactivate_and_reactivate_category(client, admin_auth_headers, db_session):
    """Test deactivating and reactivating a category via is_active patch."""
    cat = Category(name="Cables", slug="cables", is_active=True)
    db_session.add(cat)
    db_session.commit()

    # Deactivate
    response = client.patch(f"/api/v1/categories/{cat.id}", json={"is_active": False}, headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Inactive excluded from public list
    public_res = client.get("/api/v1/categories")
    assert "cables" not in [c["slug"] for c in public_res.json()]

    # Reactivate
    response = client.patch(f"/api/v1/categories/{cat.id}", json={"is_active": True}, headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_admin_can_include_inactive_categories(client, admin_auth_headers, customer_auth_headers, db_session):
    """Test that admin can view inactive categories with include_inactive=true, while customer is denied."""
    cat = Category(name="Archived Category", slug="archived-category", is_active=False)
    db_session.add(cat)
    db_session.commit()

    # Admin requests with include_inactive
    res_admin = client.get("/api/v1/categories?include_inactive=true", headers=admin_auth_headers)
    assert res_admin.status_code == 200
    assert "archived-category" in [c["slug"] for c in res_admin.json()]

    # Customer requesting include_inactive is forbidden
    res_customer = client.get("/api/v1/categories?include_inactive=true", headers=customer_auth_headers)
    assert res_customer.status_code == 403


def test_missing_category_returns_404(client):
    """Test requesting non-existent category returns 404."""
    response = client.get("/api/v1/categories/99999")
    assert response.status_code == 404


def test_delete_category_as_admin(client, admin_auth_headers, db_session):
    """Test deleting a category permanently as admin."""
    cat = Category(name="Temp Category", slug="temp-category", is_active=True)
    db_session.add(cat)
    db_session.commit()

    response = client.delete(f"/api/v1/categories/{cat.id}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    assert db_session.query(Category).filter(Category.id == cat.id).first() is None
