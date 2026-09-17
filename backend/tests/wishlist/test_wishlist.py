from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, hash_password
from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.inventory.models import Inventory
from app.modules.products.models import Product, ProductStatus
from app.modules.users.models import User, UserRole
from app.modules.wishlist.models import Wishlist, WishlistItem


@pytest.fixture
def test_category(db_session):
    cat = Category(name="Components", slug="components", is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def test_brand(db_session):
    brand = Brand(name="AMD", slug="amd", is_active=True)
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def active_product(db_session, test_category, test_brand):
    prod = Product(
        sku="CPU-RYZEN-7800X3D",
        name="AMD Ryzen 7 7800X3D",
        slug="amd-ryzen-7-7800x3d",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("449.99"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    inv = Inventory(
        product_id=prod.id,
        quantity=10,
        reserved_quantity=0,
        low_stock_threshold=3,
    )
    db_session.add(inv)
    db_session.commit()
    return prod


@pytest.fixture
def second_product(db_session, test_category, test_brand):
    prod = Product(
        sku="GPU-RADEON-7900XTX",
        name="AMD Radeon RX 7900 XTX",
        slug="amd-radeon-rx-7900-xtx",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("999.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    inv = Inventory(
        product_id=prod.id,
        quantity=5,
        reserved_quantity=0,
        low_stock_threshold=2,
    )
    db_session.add(inv)
    db_session.commit()
    return prod


@pytest.fixture
def second_customer(db_session):
    user = User(
        email="customer2@example.com",
        password_hash=hash_password("Password123!"),
        first_name="Bob",
        last_name="Smith",
        role=UserRole.CUSTOMER.value,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_customer_headers(second_customer):
    token = create_access_token(
        subject=second_customer.id,
        role=second_customer.role,
    )
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------
# 1. Wishlist Creation & Retrieval
# --------------------------------------------------------------------------

def test_get_empty_wishlist_lazy_creation(client, customer_auth_headers, test_customer_user):
    """Retrieving wishlist for the first time lazily creates an empty wishlist."""
    res = client.get("/api/v1/wishlist", headers=customer_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == test_customer_user.id
    assert data["items"] == []
    assert data["item_count"] == 0
    assert "id" in data


def test_get_wishlist_reused(client, customer_auth_headers):
    """Repeated calls return the same wishlist entity."""
    res1 = client.get("/api/v1/wishlist", headers=customer_auth_headers)
    res2 = client.get("/api/v1/wishlist", headers=customer_auth_headers)
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json()["id"] == res2.json()["id"]


# --------------------------------------------------------------------------
# 2. Adding Items
# --------------------------------------------------------------------------

def test_add_active_product_to_wishlist(client, customer_auth_headers, active_product):
    """Customer can successfully add an active product to their wishlist."""
    res = client.post(
        "/api/v1/wishlist/items",
        json={"product_id": active_product.id},
        headers=customer_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["item_count"] == 1
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["product_id"] == active_product.id
    assert item["product"]["name"] == "AMD Ryzen 7 7800X3D"
    assert item["product"]["sku"] == "CPU-RYZEN-7800X3D"
    assert item["product"]["price"] == "449.99"
    assert item["product"]["brand"]["name"] == "AMD"
    assert item["product"]["category"]["name"] == "Components"
    assert item["product"]["availability_status"] == "IN_STOCK"
    assert item["product"]["is_available"] is True


def test_add_nonexistent_product_rejected(client, customer_auth_headers):
    """Attempting to add a nonexistent product returns 404."""
    res = client.post(
        "/api/v1/wishlist/items",
        json={"product_id": 99999},
        headers=customer_auth_headers,
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_add_inactive_product_rejected(client, customer_auth_headers, db_session, test_category, test_brand):
    """Attempting to add an inactive/draft product returns 400."""
    draft_product = Product(
        sku="CPU-DRAFT",
        name="Draft CPU",
        slug="draft-cpu",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("199.99"),
        status=ProductStatus.DRAFT.value,
        is_active=False,
    )
    db_session.add(draft_product)
    db_session.commit()

    res = client.post(
        "/api/v1/wishlist/items",
        json={"product_id": draft_product.id},
        headers=customer_auth_headers,
    )
    assert res.status_code == 400
    assert "inactive or draft" in res.json()["detail"].lower()


def test_add_duplicate_product_idempotent(client, customer_auth_headers, active_product, db_session):
    """Adding the same product multiple times is idempotent and creates exactly one item."""
    # First addition
    res1 = client.post(
        "/api/v1/wishlist/items",
        json={"product_id": active_product.id},
        headers=customer_auth_headers,
    )
    assert res1.status_code == 200
    assert res1.json()["item_count"] == 1

    # Second addition
    res2 = client.post(
        "/api/v1/wishlist/items",
        json={"product_id": active_product.id},
        headers=customer_auth_headers,
    )
    assert res2.status_code == 200
    assert res2.json()["item_count"] == 1

    # Verify database directly
    items = db_session.query(WishlistItem).filter(WishlistItem.product_id == active_product.id).all()
    assert len(items) == 1


def test_database_uniqueness_enforced(db_session, test_customer_user, active_product):
    """Database unique constraint on (wishlist_id, product_id) prevents duplicates."""
    wishlist = Wishlist(user_id=test_customer_user.id)
    db_session.add(wishlist)
    db_session.commit()

    item1 = WishlistItem(wishlist_id=wishlist.id, product_id=active_product.id)
    db_session.add(item1)
    db_session.commit()

    item2 = WishlistItem(wishlist_id=wishlist.id, product_id=active_product.id)
    db_session.add(item2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# --------------------------------------------------------------------------
# 3. Removing Items
# --------------------------------------------------------------------------

def test_remove_wishlist_item_success(client, customer_auth_headers, active_product, second_product):
    """Customer can remove an item from their wishlist."""
    # Add two items
    client.post("/api/v1/wishlist/items", json={"product_id": active_product.id}, headers=customer_auth_headers)
    add_res = client.post("/api/v1/wishlist/items", json={"product_id": second_product.id}, headers=customer_auth_headers)
    data = add_res.json()
    assert data["item_count"] == 2

    item_to_remove = next(i for i in data["items"] if i["product_id"] == active_product.id)

    del_res = client.delete(f"/api/v1/wishlist/items/{item_to_remove['id']}", headers=customer_auth_headers)
    assert del_res.status_code == 200
    rem_data = del_res.json()
    assert rem_data["item_count"] == 1
    assert rem_data["items"][0]["product_id"] == second_product.id


def test_remove_nonexistent_item_returns_404(client, customer_auth_headers):
    """Removing a nonexistent item returns 404 Not Found."""
    res = client.delete("/api/v1/wishlist/items/99999", headers=customer_auth_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_customer_cannot_remove_other_customer_item(
    client, customer_auth_headers, second_customer_headers, active_product
):
    """A customer cannot delete another customer's wishlist item (returns 404 for isolation)."""
    # Customer A adds item
    res = client.post("/api/v1/wishlist/items", json={"product_id": active_product.id}, headers=customer_auth_headers)
    item_id = res.json()["items"][0]["id"]

    # Customer B attempts deletion
    del_res = client.delete(f"/api/v1/wishlist/items/{item_id}", headers=second_customer_headers)
    assert del_res.status_code == 404
    assert "not found" in del_res.json()["detail"].lower()

    # Verify Customer A still has the item
    check_res = client.get("/api/v1/wishlist", headers=customer_auth_headers)
    assert check_res.json()["item_count"] == 1


# --------------------------------------------------------------------------
# 4. Role-Based Authorization
# --------------------------------------------------------------------------

def test_unauthenticated_access_rejected(client, active_product):
    """Unauthenticated requests are rejected with 401 Unauthorized."""
    assert client.get("/api/v1/wishlist").status_code == 401
    assert client.post("/api/v1/wishlist/items", json={"product_id": active_product.id}).status_code == 401
    assert client.delete("/api/v1/wishlist/items/1").status_code == 401
    assert client.get(f"/api/v1/wishlist/check/{active_product.id}").status_code == 401


def test_admin_access_rejected(client, admin_auth_headers, active_product):
    """Admin requests are forbidden with 403 Forbidden."""
    assert client.get("/api/v1/wishlist", headers=admin_auth_headers).status_code == 403
    assert client.post("/api/v1/wishlist/items", json={"product_id": active_product.id}, headers=admin_auth_headers).status_code == 403
    assert client.delete("/api/v1/wishlist/items/1", headers=admin_auth_headers).status_code == 403
    assert client.get(f"/api/v1/wishlist/check/{active_product.id}", headers=admin_auth_headers).status_code == 403


# --------------------------------------------------------------------------
# 5. Product Availability & State Changes
# --------------------------------------------------------------------------

def test_product_becoming_inactive_preserved_in_wishlist(client, customer_auth_headers, active_product, db_session):
    """Existing wishlisted products that become inactive remain in the wishlist with UNAVAILABLE status."""
    # Add active product
    client.post("/api/v1/wishlist/items", json={"product_id": active_product.id}, headers=customer_auth_headers)

    # Deactivate product
    active_product.is_active = False
    active_product.status = ProductStatus.ARCHIVED.value
    db_session.commit()

    # Retrieve wishlist
    res = client.get("/api/v1/wishlist", headers=customer_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["item_count"] == 1
    item = data["items"][0]
    assert item["product"]["is_available"] is False
    assert item["product"]["availability_status"] == "UNAVAILABLE"


def test_out_of_stock_product_shows_out_of_stock_status(client, customer_auth_headers, db_session, test_category, test_brand):
    """Wishlisted product with 0 inventory displays OUT_OF_STOCK."""
    prod = Product(
        sku="CPU-OOS",
        name="Out of Stock CPU",
        slug="out-of-stock-cpu",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("299.99"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()
    inv = Inventory(product_id=prod.id, quantity=0, reserved_quantity=0, low_stock_threshold=2)
    db_session.add(inv)
    db_session.commit()

    client.post("/api/v1/wishlist/items", json={"product_id": prod.id}, headers=customer_auth_headers)
    res = client.get("/api/v1/wishlist", headers=customer_auth_headers)
    assert res.status_code == 200
    item = res.json()["items"][0]
    assert item["product"]["is_available"] is False
    assert item["product"]["availability_status"] == "OUT_OF_STOCK"


# --------------------------------------------------------------------------
# 6. Check Endpoint
# --------------------------------------------------------------------------

def test_check_endpoint_wishlisted_true_and_false(client, customer_auth_headers, active_product):
    """Check endpoint reports is_wishlisted boolean and item id accurately."""
    # Before adding
    res_before = client.get(f"/api/v1/wishlist/check/{active_product.id}", headers=customer_auth_headers)
    assert res_before.status_code == 200
    assert res_before.json()["is_wishlisted"] is False
    assert res_before.json()["wishlist_item_id"] is None

    # Add product
    client.post("/api/v1/wishlist/items", json={"product_id": active_product.id}, headers=customer_auth_headers)

    # After adding
    res_after = client.get(f"/api/v1/wishlist/check/{active_product.id}", headers=customer_auth_headers)
    assert res_after.status_code == 200
    assert res_after.json()["is_wishlisted"] is True
    assert isinstance(res_after.json()["wishlist_item_id"], int)


# --------------------------------------------------------------------------
# 7. Inventory Isolation
# --------------------------------------------------------------------------

def test_wishlist_operations_do_not_modify_inventory(client, customer_auth_headers, active_product, db_session):
    """Wishlist additions and removals never modify inventory quantities or reservations."""
    inv = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first()
    initial_qty = inv.quantity
    initial_reserved = inv.reserved_quantity

    # Add to wishlist
    add_res = client.post("/api/v1/wishlist/items", json={"product_id": active_product.id}, headers=customer_auth_headers)
    item_id = add_res.json()["items"][0]["id"]

    db_session.refresh(inv)
    assert inv.quantity == initial_qty
    assert inv.reserved_quantity == initial_reserved

    # Remove from wishlist
    client.delete(f"/api/v1/wishlist/items/{item_id}", headers=customer_auth_headers)

    db_session.refresh(inv)
    assert inv.quantity == initial_qty
    assert inv.reserved_quantity == initial_reserved


# --------------------------------------------------------------------------
# 8. Cascading Deletion Behavior
# --------------------------------------------------------------------------

def test_product_deletion_cascades_to_wishlist_items(client, customer_auth_headers, active_product, db_session):
    """Deleting a product cascades to remove associated wishlist items without leaving orphaned rows."""
    client.post("/api/v1/wishlist/items", json={"product_id": active_product.id}, headers=customer_auth_headers)

    prod_id = active_product.id
    assert db_session.query(WishlistItem).filter(WishlistItem.product_id == prod_id).count() == 1

    db_session.delete(active_product)
    db_session.commit()

    assert db_session.query(WishlistItem).filter(WishlistItem.product_id == prod_id).count() == 0


def test_user_deletion_cascades_to_wishlist(client, second_customer_headers, second_customer, active_product, db_session):
    """Deleting a user cascades to remove their wishlist and all items."""
    client.post("/api/v1/wishlist/items", json={"product_id": active_product.id}, headers=second_customer_headers)

    user_id = second_customer.id
    wishlist = db_session.query(Wishlist).filter(Wishlist.user_id == user_id).first()
    assert wishlist is not None

    db_session.delete(second_customer)
    db_session.commit()

    assert db_session.query(Wishlist).filter(Wishlist.user_id == user_id).first() is None
    assert db_session.query(WishlistItem).filter(WishlistItem.wishlist_id == wishlist.id).count() == 0
