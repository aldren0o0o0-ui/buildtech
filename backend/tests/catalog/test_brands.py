import pytest
from app.modules.catalog.brand_model import Brand


def test_public_list_active_brands(client, db_session):
    """Test public listing returns only active brands."""
    b1 = Brand(name="NVIDIA", slug="nvidia", is_active=True)
    b2 = Brand(name="AMD", slug="amd", is_active=True)
    b3 = Brand(name="Obsolete Brand", slug="obsolete-brand", is_active=False)
    db_session.add_all([b1, b2, b3])
    db_session.commit()

    response = client.get("/api/v1/brands")
    assert response.status_code == 200
    data = response.json()
    slugs = [b["slug"] for b in data]
    assert "amd" in slugs
    assert "nvidia" in slugs
    assert "obsolete-brand" not in slugs


def test_get_brand_by_id(client, db_session):
    """Test retrieving a single active brand by ID."""
    brand = Brand(name="Intel", slug="intel", description="Processors & Arc GPUs", is_active=True)
    db_session.add(brand)
    db_session.commit()

    response = client.get(f"/api/v1/brands/{brand.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == brand.id
    assert data["name"] == "Intel"
    assert data["slug"] == "intel"
    assert data["description"] == "Processors & Arc GPUs"


def test_create_brand_as_admin(client, admin_auth_headers, db_session):
    """Test creating a brand as an authenticated ADMIN."""
    payload = {
        "name": "Corsair",
        "description": "Gaming peripherals, memory, and PSUs",
        "logo_url": "https://example.com/corsair-logo.png",
        "is_active": True,
    }
    response = client.post("/api/v1/brands", json=payload, headers=admin_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Corsair"
    assert data["slug"] == "corsair"
    assert data["logo_url"] == "https://example.com/corsair-logo.png"
    assert data["is_active"] is True

    # Verify in DB
    db_brand = db_session.query(Brand).filter(Brand.slug == "corsair").first()
    assert db_brand is not None


def test_customer_cannot_create_brand(client, customer_auth_headers):
    """Test that a CUSTOMER user receives 403 when attempting to create a brand."""
    payload = {"name": "ASUS"}
    response = client.post("/api/v1/brands", json=payload, headers=customer_auth_headers)
    assert response.status_code == 403


def test_unauthenticated_cannot_create_brand(client):
    """Test that unauthenticated request receives 401 when attempting to create a brand."""
    payload = {"name": "MSI"}
    response = client.post("/api/v1/brands", json=payload)
    assert response.status_code == 401


def test_duplicate_brand_name_rejected(client, admin_auth_headers, db_session):
    """Test that creating a brand with an existing name is rejected."""
    brand = Brand(name="Gigabyte", slug="gigabyte", is_active=True)
    db_session.add(brand)
    db_session.commit()

    payload = {"name": "  GIGABYTE  "}
    response = client.post("/api/v1/brands", json=payload, headers=admin_auth_headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_brand_slug_generated_deterministically(client, admin_auth_headers):
    """Test slug is cleaned, lowercased, and hyphens applied."""
    payload = {"name": "  Western Digital (WD)  "}
    response = client.post("/api/v1/brands", json=payload, headers=admin_auth_headers)
    assert response.status_code == 201
    assert response.json()["slug"] == "western-digital-wd"


def test_update_brand(client, admin_auth_headers, db_session):
    """Test updating a brand's name, description, and logo_url."""
    brand = Brand(name="Kingston", slug="kingston", is_active=True)
    db_session.add(brand)
    db_session.commit()

    payload = {
        "name": "Kingston Technology",
        "description": "RAM and Flash Storage",
        "logo_url": "https://example.com/kingston.svg",
    }
    response = client.patch(f"/api/v1/brands/{brand.id}", json=payload, headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Kingston Technology"
    assert data["slug"] == "kingston-technology"
    assert data["description"] == "RAM and Flash Storage"
    assert data["logo_url"] == "https://example.com/kingston.svg"


def test_deactivate_and_reactivate_brand(client, admin_auth_headers, db_session):
    """Test deactivating and reactivating a brand via is_active patch."""
    brand = Brand(name="EVGA", slug="evga", is_active=True)
    db_session.add(brand)
    db_session.commit()

    # Deactivate
    response = client.patch(f"/api/v1/brands/{brand.id}", json={"is_active": False}, headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Inactive excluded from public list
    public_res = client.get("/api/v1/brands")
    assert "evga" not in [b["slug"] for b in public_res.json()]

    # Reactivate
    response = client.patch(f"/api/v1/brands/{brand.id}", json={"is_active": True}, headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_admin_can_include_inactive_brands(client, admin_auth_headers, customer_auth_headers, db_session):
    """Test that admin can view inactive brands with include_inactive=true, while customer is denied."""
    brand = Brand(name="Legacy Brand", slug="legacy-brand", is_active=False)
    db_session.add(brand)
    db_session.commit()

    # Admin requests with include_inactive
    res_admin = client.get("/api/v1/brands?include_inactive=true", headers=admin_auth_headers)
    assert res_admin.status_code == 200
    assert "legacy-brand" in [b["slug"] for b in res_admin.json()]

    # Customer requesting include_inactive is forbidden
    res_customer = client.get("/api/v1/brands?include_inactive=true", headers=customer_auth_headers)
    assert res_customer.status_code == 403


def test_missing_brand_returns_404(client):
    """Test requesting non-existent brand returns 404."""
    response = client.get("/api/v1/brands/99999")
    assert response.status_code == 404


def test_delete_brand_as_admin(client, admin_auth_headers, db_session):
    """Test deleting a brand permanently as admin."""
    brand = Brand(name="Temporary Brand", slug="temporary-brand", is_active=True)
    db_session.add(brand)
    db_session.commit()

    response = client.delete(f"/api/v1/brands/{brand.id}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    assert db_session.query(Brand).filter(Brand.id == brand.id).first() is None
