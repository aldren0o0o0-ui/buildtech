from decimal import Decimal
import pytest
from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.products.models import Product, ProductStatus


@pytest.fixture
def test_category(db_session):
    cat = Category(name="Graphics Cards", slug="graphics-cards", is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def test_brand(db_session):
    brand = Brand(name="NVIDIA", slug="nvidia", is_active=True)
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def test_inactive_category(db_session):
    cat = Category(name="Legacy Disks", slug="legacy-disks", is_active=False)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def test_inactive_brand(db_session):
    brand = Brand(name="Legacy Maker", slug="legacy-maker", is_active=False)
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


def test_public_list_active_products(client, db_session, test_category, test_brand):
    """Test public listing returns only active products with status='ACTIVE'."""
    p1 = Product(
        sku="GPU-001",
        name="GeForce RTX 4070 Super",
        slug="geforce-rtx-4070-super",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("599.99"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    p2_draft = Product(
        sku="GPU-002",
        name="GeForce RTX 5090",
        slug="geforce-rtx-5090",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("1999.99"),
        status=ProductStatus.DRAFT.value,
        is_active=True,
    )
    p3_archived = Product(
        sku="GPU-003",
        name="GeForce GTX 1080",
        slug="geforce-gtx-1080",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("299.99"),
        status=ProductStatus.ARCHIVED.value,
        is_active=True,
    )
    p4_inactive = Product(
        sku="GPU-004",
        name="GeForce RTX 3060",
        slug="geforce-rtx-3060",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("289.99"),
        status=ProductStatus.ACTIVE.value,
        is_active=False,
    )
    db_session.add_all([p1, p2_draft, p3_archived, p4_inactive])
    db_session.commit()

    response = client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    skus = [p["sku"] for p in data]
    assert "GPU-001" in skus
    assert "GPU-002" not in skus
    assert "GPU-003" not in skus
    assert "GPU-004" not in skus


def test_get_product_by_slug_and_id(client, db_session, test_category, test_brand):
    """Test retrieving active product by slug and by numeric ID."""
    product = Product(
        sku="GPU-010",
        name="GeForce RTX 4080 Super",
        slug="geforce-rtx-4080-super",
        description="High-end 4K gaming graphics card",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("999.99"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    # By slug
    res_slug = client.get(f"/api/v1/products/{product.slug}")
    assert res_slug.status_code == 200
    data = res_slug.json()
    assert data["sku"] == "GPU-010"
    assert data["name"] == "GeForce RTX 4080 Super"
    assert data["category"]["name"] == "Graphics Cards"
    assert data["brand"]["name"] == "NVIDIA"

    # By ID
    res_id = client.get(f"/api/v1/products/{product.id}")
    assert res_id.status_code == 200
    assert res_id.json()["slug"] == "geforce-rtx-4080-super"


def test_missing_product_returns_404(client):
    """Test requesting non-existent product returns 404."""
    response = client.get("/api/v1/products/non-existent-product-slug")
    assert response.status_code == 404


def test_create_product_as_admin(client, admin_auth_headers, db_session, test_category, test_brand):
    """Test creating product as admin with valid parameters."""
    payload = {
        "sku": "GPU-020",
        "name": "GeForce RTX 4060 Ti",
        "description": "1080p and 1440p gaming card",
        "category_id": test_category.id,
        "brand_id": test_brand.id,
        "price": "399.00",
        "image_url": "https://example.com/rtx4060ti.png",
        "status": "ACTIVE",
        "is_active": True,
    }
    response = client.post("/api/v1/products", json=payload, headers=admin_auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "GPU-020"
    assert data["name"] == "GeForce RTX 4060 Ti"
    assert data["slug"] == "geforce-rtx-4060-ti"
    assert float(data["price"]) == 399.00
    assert data["status"] == "ACTIVE"


def test_customer_cannot_create_product(client, customer_auth_headers, test_category, test_brand):
    """Test that customer user receives 403 when creating product."""
    payload = {
        "sku": "GPU-021",
        "name": "GeForce RTX 4060",
        "category_id": test_category.id,
        "brand_id": test_brand.id,
        "price": "299.00",
    }
    response = client.post("/api/v1/products", json=payload, headers=customer_auth_headers)
    assert response.status_code == 403


def test_unauthenticated_cannot_create_product(client, test_category, test_brand):
    """Test that unauthenticated request receives 401."""
    payload = {
        "sku": "GPU-022",
        "name": "GeForce RTX 4060",
        "category_id": test_category.id,
        "brand_id": test_brand.id,
        "price": "299.00",
    }
    response = client.post("/api/v1/products", json=payload)
    assert response.status_code == 401


def test_duplicate_sku_rejected(client, admin_auth_headers, db_session, test_category, test_brand):
    """Test creating product with existing SKU is rejected."""
    p = Product(
        sku="SKU-DUP-1",
        name="Card One",
        slug="card-one",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("100.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(p)
    db_session.commit()

    payload = {
        "sku": "SKU-DUP-1",
        "name": "Card Two",
        "category_id": test_category.id,
        "brand_id": test_brand.id,
        "price": "150.00",
    }
    response = client.post("/api/v1/products", json=payload, headers=admin_auth_headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_invalid_category_or_brand_rejected(client, admin_auth_headers, test_category, test_brand):
    """Test that non-existent category or brand IDs are rejected."""
    # Invalid Category
    res_cat = client.post(
        "/api/v1/products",
        json={"sku": "SKU-INV-1", "name": "Prod 1", "category_id": 99999, "brand_id": test_brand.id, "price": "100.00"},
        headers=admin_auth_headers,
    )
    assert res_cat.status_code == 400
    assert "Category with ID 99999 does not exist" in res_cat.json()["detail"]

    # Invalid Brand
    res_brand = client.post(
        "/api/v1/products",
        json={"sku": "SKU-INV-2", "name": "Prod 2", "category_id": test_category.id, "brand_id": 99999, "price": "100.00"},
        headers=admin_auth_headers,
    )
    assert res_brand.status_code == 400
    assert "Brand with ID 99999 does not exist" in res_brand.json()["detail"]


def test_inactive_category_or_brand_rejected(client, admin_auth_headers, test_inactive_category, test_inactive_brand, test_category, test_brand):
    """Test creating products with inactive category or brand is rejected."""
    # Inactive Category
    res1 = client.post(
        "/api/v1/products",
        json={"sku": "SKU-INACT-1", "name": "P1", "category_id": test_inactive_category.id, "brand_id": test_brand.id, "price": "10.00"},
        headers=admin_auth_headers,
    )
    assert res1.status_code == 400
    assert "inactive and cannot be assigned" in res1.json()["detail"]

    # Inactive Brand
    res2 = client.post(
        "/api/v1/products",
        json={"sku": "SKU-INACT-2", "name": "P2", "category_id": test_category.id, "brand_id": test_inactive_brand.id, "price": "10.00"},
        headers=admin_auth_headers,
    )
    assert res2.status_code == 400
    assert "inactive and cannot be assigned" in res2.json()["detail"]


def test_negative_price_rejected(client, admin_auth_headers, test_category, test_brand):
    """Test schema rejects negative price."""
    payload = {
        "sku": "SKU-NEG",
        "name": "Invalid Price Card",
        "category_id": test_category.id,
        "brand_id": test_brand.id,
        "price": "-50.00",
    }
    response = client.post("/api/v1/products", json=payload, headers=admin_auth_headers)
    assert response.status_code == 422


def test_update_product(client, admin_auth_headers, db_session, test_category, test_brand):
    """Test updating product fields, name/slug regeneration, and price."""
    product = Product(
        sku="GPU-UPD",
        name="Original Product Name",
        slug="original-product-name",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("500.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    payload = {
        "name": "Updated Super Product",
        "price": "549.99",
        "status": "DRAFT",
    }
    response = client.patch(f"/api/v1/products/{product.id}", json=payload, headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Super Product"
    assert data["slug"] == "updated-super-product"
    assert float(data["price"]) == 549.99
    assert data["status"] == "DRAFT"


def test_search_and_filter_products(client, db_session, test_category, test_brand):
    """Test searching by keyword and filtering by category, brand, and price range."""
    # Secondary category & brand
    cpu_cat = Category(name="Processors", slug="processors", is_active=True)
    intel_brand = Brand(name="Intel", slug="intel", is_active=True)
    db_session.add_all([cpu_cat, intel_brand])
    db_session.commit()

    p1 = Product(
        sku="GPU-SRCH-1",
        name="ASUS ROG Strix RTX 4070",
        slug="asus-rog-strix-rtx-4070",
        description="High quality GPU",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("650.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    p2 = Product(
        sku="CPU-SRCH-2",
        name="Intel Core i7-14700K",
        slug="intel-core-i7-14700k",
        description="LGA1700 desktop processor",
        category_id=cpu_cat.id,
        brand_id=intel_brand.id,
        price=Decimal("400.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add_all([p1, p2])
    db_session.commit()

    # Search by text
    res_search = client.get("/api/v1/products?search=i7-14700k")
    assert len(res_search.json()) == 1
    assert res_search.json()[0]["sku"] == "CPU-SRCH-2"

    # Filter by category
    res_cat = client.get(f"/api/v1/products?category_id={cpu_cat.id}")
    assert len(res_cat.json()) == 1
    assert res_cat.json()[0]["sku"] == "CPU-SRCH-2"

    # Filter by brand
    res_brand = client.get(f"/api/v1/products?brand_id={test_brand.id}")
    assert len(res_brand.json()) == 1
    assert res_brand.json()[0]["sku"] == "GPU-SRCH-1"

    # Filter by price range
    res_price = client.get("/api/v1/products?min_price=500&max_price=700")
    assert len(res_price.json()) == 1
    assert res_price.json()[0]["sku"] == "GPU-SRCH-1"


def test_sort_products(client, db_session, test_category, test_brand):
    """Test sorting products by price ascending and descending."""
    p_cheap = Product(
        sku="SORT-1",
        name="A Cheap Item",
        slug="a-cheap-item",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("50.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    p_expensive = Product(
        sku="SORT-2",
        name="Z Expensive Item",
        slug="z-expensive-item",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("500.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add_all([p_cheap, p_expensive])
    db_session.commit()

    # Price ASC
    res_asc = client.get("/api/v1/products?sort=price_asc")
    assert res_asc.json()[0]["sku"] == "SORT-1"

    # Price DESC
    res_desc = client.get("/api/v1/products?sort=price_desc")
    assert res_desc.json()[0]["sku"] == "SORT-2"


def test_category_with_product_cannot_be_deleted(client, admin_auth_headers, db_session, test_category, test_brand):
    """Test that category deletion is blocked if products are attached to it."""
    product = Product(
        sku="PROD-CAT-BLOCK",
        name="Some GPU",
        slug="some-gpu",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("200.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    response = client.delete(f"/api/v1/categories/{test_category.id}", headers=admin_auth_headers)
    assert response.status_code == 400
    assert "attached to it" in response.json()["detail"]


def test_brand_with_product_cannot_be_deleted(client, admin_auth_headers, db_session, test_category, test_brand):
    """Test that brand deletion is blocked if products are attached to it."""
    product = Product(
        sku="PROD-BRAND-BLOCK",
        name="Some Brand GPU",
        slug="some-brand-gpu",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("200.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    response = client.delete(f"/api/v1/brands/{test_brand.id}", headers=admin_auth_headers)
    assert response.status_code == 400
    assert "attached to it" in response.json()["detail"]


def test_delete_product_as_admin(client, admin_auth_headers, db_session, test_category, test_brand):
    """Test deleting product as admin."""
    product = Product(
        sku="PROD-DEL",
        name="Delete Me GPU",
        slug="delete-me-gpu",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("150.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()

    response = client.delete(f"/api/v1/products/{product.id}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"]

    assert db_session.query(Product).filter(Product.id == product.id).first() is None
