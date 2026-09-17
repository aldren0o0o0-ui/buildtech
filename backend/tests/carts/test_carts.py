from decimal import Decimal
import pytest

from app.core.security import create_access_token, hash_password
from app.modules.carts.models import Cart, CartItem
from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.inventory.models import Inventory
from app.modules.products.models import Product, ProductStatus
from app.modules.users.models import User, UserRole


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

    # Add inventory of 10 available units
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
        price=Decimal("899.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    # Add inventory of 5 available units
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
def second_customer_auth_headers(second_customer):
    token = create_access_token(
        subject=second_customer.id,
        role=second_customer.role,
    )
    return {"Authorization": f"Bearer {token}"}


# ==========================================
# 1. Cart Retrieval & Lazy Initialization
# ==========================================

def test_get_cart_lazily_initializes_empty_cart(client, customer_auth_headers, test_customer_user, db_session):
    """Test retrieving cart creates a new cart row if none exists and returns empty structure."""
    res = client.get("/api/v1/cart", headers=customer_auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["items"] == []
    assert Decimal(data["subtotal"]) == Decimal("0.00")
    assert data["item_count"] == 0
    assert data["total_quantity"] == 0

    # Verify Cart row was created in DB
    cart = db_session.query(Cart).filter(Cart.user_id == test_customer_user.id).first()
    assert cart is not None
    assert cart.id == data["id"]


def test_get_cart_returns_same_cart_instance(client, customer_auth_headers, test_customer_user, db_session):
    """Test subsequent requests reuse the existing Cart entity."""
    res1 = client.get("/api/v1/cart", headers=customer_auth_headers)
    res2 = client.get("/api/v1/cart", headers=customer_auth_headers)
    assert res1.json()["id"] == res2.json()["id"]

    count = db_session.query(Cart).filter(Cart.user_id == test_customer_user.id).count()
    assert count == 1


# ==========================================
# 2. Adding Products to Cart
# ==========================================

def test_add_active_product_to_cart_success(client, customer_auth_headers, active_product, db_session):
    """Test adding an active product with sufficient stock succeeds."""
    payload = {"product_id": active_product.id, "quantity": 2}
    res = client.post("/api/v1/cart/items", json=payload, headers=customer_auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["item_count"] == 1
    assert data["total_quantity"] == 2
    assert Decimal(data["subtotal"]) == Decimal("449.99") * 2

    item = data["items"][0]
    assert item["product"]["id"] == active_product.id
    assert item["product"]["name"] == active_product.name
    assert item["product"]["brand"]["name"] == "AMD"
    assert item["quantity"] == 2
    assert item["is_available"] is True
    assert item["availability_status"] == "AVAILABLE"
    assert Decimal(item["item_subtotal"]) == Decimal("899.98")


def test_add_same_product_accumulates_quantity(client, customer_auth_headers, active_product, db_session):
    """Test adding the same product again increases quantity and does not create duplicate rows."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)
    res = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 3}, headers=customer_auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["item_count"] == 1
    assert data["total_quantity"] == 5
    assert data["items"][0]["quantity"] == 5

    # Check DB rows
    cart_items = db_session.query(CartItem).all()
    assert len(cart_items) == 1
    assert cart_items[0].quantity == 5


def test_add_different_products_creates_separate_items(client, customer_auth_headers, active_product, second_product):
    """Test adding two distinct products results in two distinct items with combined totals."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)
    res = client.post("/api/v1/cart/items", json={"product_id": second_product.id, "quantity": 1}, headers=customer_auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["item_count"] == 2
    assert data["total_quantity"] == 3
    expected_subtotal = (Decimal("449.99") * 2) + (Decimal("899.00") * 1)
    assert Decimal(data["subtotal"]) == expected_subtotal


def test_add_nonexistent_product_returns_404(client, customer_auth_headers):
    """Test adding a non-existent product ID returns 404."""
    res = client.post("/api/v1/cart/items", json={"product_id": 99999, "quantity": 1}, headers=customer_auth_headers)
    assert res.status_code == 404


def test_add_inactive_product_returns_400(client, customer_auth_headers, test_category, test_brand, db_session):
    """Test adding an inactive or draft product is rejected with 400."""
    draft_prod = Product(
        sku="DRAFT-ITEM",
        name="Unreleased CPU",
        slug="unreleased-cpu",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("500.00"),
        status=ProductStatus.DRAFT.value,
        is_active=True,
    )
    db_session.add(draft_prod)
    db_session.commit()

    res = client.post("/api/v1/cart/items", json={"product_id": draft_prod.id, "quantity": 1}, headers=customer_auth_headers)
    assert res.status_code == 400
    assert "inactive or unavailable" in res.json()["detail"].lower()


def test_add_invalid_quantities_rejected(client, customer_auth_headers, active_product):
    """Test zero or negative quantities are rejected with 422 Unprocessable Entity."""
    res_zero = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 0}, headers=customer_auth_headers)
    assert res_zero.status_code == 422

    res_neg = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": -3}, headers=customer_auth_headers)
    assert res_neg.status_code == 422


def test_add_quantity_exceeding_inventory_rejected(client, customer_auth_headers, active_product):
    """Test adding more units than available inventory returns 400."""
    # Available is 10
    res = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 15}, headers=customer_auth_headers)
    assert res.status_code == 400
    assert "available in stock" in res.json()["detail"].lower()


def test_accumulated_quantity_exceeding_inventory_rejected(client, customer_auth_headers, active_product):
    """Test second add exceeding stock returns 400 with helpful message."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 8}, headers=customer_auth_headers)
    res = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 5}, headers=customer_auth_headers)
    assert res.status_code == 400
    assert "8 already in your cart" in res.json()["detail"]


# ==========================================
# 3. Updating Cart Item Quantity
# ==========================================

def test_update_cart_item_quantity_success(client, customer_auth_headers, active_product):
    """Test updating cart item quantity modifies subtotal and total units."""
    add_res = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)
    item_id = add_res.json()["items"][0]["id"]

    update_res = client.patch(f"/api/v1/cart/items/{item_id}", json={"quantity": 4}, headers=customer_auth_headers)
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["total_quantity"] == 4
    assert data["items"][0]["quantity"] == 4
    assert Decimal(data["subtotal"]) == Decimal("449.99") * 4


def test_update_cart_item_exceeding_stock_rejected(client, customer_auth_headers, active_product):
    """Test updating item quantity beyond available inventory returns 400."""
    add_res = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)
    item_id = add_res.json()["items"][0]["id"]

    res = client.patch(f"/api/v1/cart/items/{item_id}", json={"quantity": 20}, headers=customer_auth_headers)
    assert res.status_code == 400
    assert "available in stock" in res.json()["detail"].lower()


def test_update_cart_item_invalid_quantity_rejected(client, customer_auth_headers, active_product):
    """Test setting quantity to 0 or negative returns 422."""
    add_res = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)
    item_id = add_res.json()["items"][0]["id"]

    res = client.patch(f"/api/v1/cart/items/{item_id}", json={"quantity": 0}, headers=customer_auth_headers)
    assert res.status_code == 422


# ==========================================
# 4. Removing Cart Item & Clearing Cart
# ==========================================

def test_remove_cart_item_success(client, customer_auth_headers, active_product, second_product):
    """Test removing a cart item deletes it and recalculates totals."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)
    res2 = client.post("/api/v1/cart/items", json={"product_id": second_product.id, "quantity": 1}, headers=customer_auth_headers)
    
    items = res2.json()["items"]
    cpu_item_id = [item["id"] for item in items if item["product"]["id"] == active_product.id][0]

    delete_res = client.delete(f"/api/v1/cart/items/{cpu_item_id}", headers=customer_auth_headers)
    assert delete_res.status_code == 200
    data = delete_res.json()

    assert data["item_count"] == 1
    assert data["total_quantity"] == 1
    assert data["items"][0]["product"]["id"] == second_product.id
    assert Decimal(data["subtotal"]) == Decimal("899.00")


def test_clear_cart_success(client, customer_auth_headers, active_product, second_product, db_session, test_customer_user):
    """Test clearing cart removes all items but keeps Cart entity intact."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"product_id": second_product.id, "quantity": 1}, headers=customer_auth_headers)

    clear_res = client.delete("/api/v1/cart", headers=customer_auth_headers)
    assert clear_res.status_code == 200
    data = clear_res.json()

    assert data["items"] == []
    assert data["item_count"] == 0
    assert data["total_quantity"] == 0
    assert Decimal(data["subtotal"]) == Decimal("0.00")

    # Cart entity is preserved
    cart = db_session.query(Cart).filter(Cart.user_id == test_customer_user.id).first()
    assert cart is not None


# ==========================================
# 5. Customer Ownership Isolation
# ==========================================

def test_customer_ownership_isolation(
    client,
    customer_auth_headers,
    second_customer_auth_headers,
    active_product,
):
    """Test Customer A cannot see, modify, or delete Customer B's cart items."""
    # Customer A adds product
    res_a = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)
    item_a_id = res_a.json()["items"][0]["id"]

    # Customer B views cart -> is empty
    res_b_view = client.get("/api/v1/cart", headers=second_customer_auth_headers)
    assert res_b_view.json()["item_count"] == 0

    # Customer B attempts to update Customer A's item -> 404
    res_b_update = client.patch(f"/api/v1/cart/items/{item_a_id}", json={"quantity": 5}, headers=second_customer_auth_headers)
    assert res_b_update.status_code == 404

    # Customer B attempts to delete Customer A's item -> 404
    res_b_delete = client.delete(f"/api/v1/cart/items/{item_a_id}", headers=second_customer_auth_headers)
    assert res_b_delete.status_code == 404


# ==========================================
# 6. Authorization & Role Checks
# ==========================================

def test_unauthenticated_cart_access_rejected(client, active_product):
    """Test unauthenticated requests are rejected with 401."""
    res_get = client.get("/api/v1/cart")
    assert res_get.status_code == 401

    res_post = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 1})
    assert res_post.status_code == 401


def test_admin_cannot_manipulate_customer_cart(client, admin_auth_headers, active_product):
    """Test Admin account receives 403 Forbidden on customer cart endpoints."""
    res_get = client.get("/api/v1/cart", headers=admin_auth_headers)
    assert res_get.status_code == 403

    res_post = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 1}, headers=admin_auth_headers)
    assert res_post.status_code == 403


# ==========================================
# 7. Dynamic Availability State Changes
# ==========================================

def test_product_deactivated_after_adding_remains_in_cart_as_unavailable(
    client,
    customer_auth_headers,
    active_product,
    db_session,
):
    """Test that if a product is deactivated, the cart item is not deleted but marked unavailable."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)

    # Deactivate product
    active_product.is_active = False
    db_session.add(active_product)
    db_session.commit()

    # View cart
    res = client.get("/api/v1/cart", headers=customer_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["is_available"] is False
    assert item["availability_status"] == "PRODUCT_UNAVAILABLE"
    assert "currently unavailable" in item["availability_reason"].lower()


def test_inventory_reduction_after_adding_marks_insufficient_stock(
    client,
    customer_auth_headers,
    active_product,
    db_session,
):
    """Test that if inventory stock drops below cart quantity, item is flagged as INSUFFICIENT_STOCK."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 5}, headers=customer_auth_headers)

    # Reduce inventory to 2
    inv = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first()
    inv.quantity = 2
    db_session.add(inv)
    db_session.commit()

    res = client.get("/api/v1/cart", headers=customer_auth_headers)
    assert res.status_code == 200
    item = res.json()["items"][0]
    assert item["is_available"] is False
    assert item["availability_status"] == "INSUFFICIENT_STOCK"
    assert "Only 2 units available" in item["availability_reason"]


# ==========================================
# 8. CRITICAL ARCHITECTURAL INVARIANT:
#    Adding/updating cart DOES NOT change inventory.reserved_quantity
# ==========================================

def test_cart_operations_do_not_mutate_inventory(
    client,
    customer_auth_headers,
    active_product,
    db_session,
):
    """Verify strictly that adding and updating cart items does not change inventory quantity or reserved_quantity."""
    inv_before = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first()
    qty_before = inv_before.quantity
    reserved_before = inv_before.reserved_quantity

    # Add 4 units to cart
    res_add = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 4}, headers=customer_auth_headers)
    assert res_add.status_code == 200
    item_id = res_add.json()["items"][0]["id"]

    db_session.refresh(inv_before)
    assert inv_before.quantity == qty_before
    assert inv_before.reserved_quantity == reserved_before

    # Update item to 6 units
    res_update = client.patch(f"/api/v1/cart/items/{item_id}", json={"quantity": 6}, headers=customer_auth_headers)
    assert res_update.status_code == 200

    db_session.refresh(inv_before)
    assert inv_before.quantity == qty_before
    assert inv_before.reserved_quantity == reserved_before


# ==========================================
# 9. Edge Cases, Cascades & Precision
# ==========================================

def test_remove_nonexistent_cart_item_returns_404(client, customer_auth_headers):
    """Test removing a nonexistent cart item ID returns 404."""
    res = client.delete("/api/v1/cart/items/99999", headers=customer_auth_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_product_deletion_cascades_to_cart_items(
    client,
    customer_auth_headers,
    active_product,
    db_session,
):
    """Test that deleting a product cascades and removes it from cart items cleanly."""
    res = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 1

    # Delete product
    db_session.delete(active_product)
    db_session.commit()

    # View cart: item is gone
    res_view = client.get("/api/v1/cart", headers=customer_auth_headers)
    assert res_view.status_code == 200
    assert res_view.json()["item_count"] == 0
    assert res_view.json()["items"] == []


def test_user_deletion_cascades_to_cart(
    client,
    customer_auth_headers,
    active_product,
    test_customer_user,
    db_session,
):
    """Test that deleting a customer cascades and removes their cart and cart items."""
    res = client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)
    assert res.status_code == 200

    cart = db_session.query(Cart).filter(Cart.user_id == test_customer_user.id).first()
    assert cart is not None
    cart_id = cart.id

    # Delete customer user
    db_session.delete(test_customer_user)
    db_session.commit()

    # Verify cart and cart items are deleted
    assert db_session.query(Cart).filter(Cart.id == cart_id).first() is None
    assert db_session.query(CartItem).filter(CartItem.cart_id == cart_id).all() == []


def test_decimal_precision_multi_item_subtotal_calculation(
    client,
    customer_auth_headers,
    test_category,
    test_brand,
    db_session,
):
    """Test exact Decimal arithmetic across multiple items to avoid floating-point inaccuracies."""
    p1 = Product(sku="ITEM-1", name="Item 1", slug="item-1", category_id=test_category.id, brand_id=test_brand.id, price=Decimal("19.99"), status=ProductStatus.ACTIVE.value, is_active=True)
    p2 = Product(sku="ITEM-2", name="Item 2", slug="item-2", category_id=test_category.id, brand_id=test_brand.id, price=Decimal("49.95"), status=ProductStatus.ACTIVE.value, is_active=True)
    p3 = Product(sku="ITEM-3", name="Item 3", slug="item-3", category_id=test_category.id, brand_id=test_brand.id, price=Decimal("109.90"), status=ProductStatus.ACTIVE.value, is_active=True)
    db_session.add_all([p1, p2, p3])
    db_session.flush()

    db_session.add_all([
        Inventory(product_id=p1.id, quantity=10, reserved_quantity=0),
        Inventory(product_id=p2.id, quantity=10, reserved_quantity=0),
        Inventory(product_id=p3.id, quantity=10, reserved_quantity=0),
    ])
    db_session.commit()

    client.post("/api/v1/cart/items", json={"product_id": p1.id, "quantity": 3}, headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"product_id": p2.id, "quantity": 7}, headers=customer_auth_headers)
    res = client.post("/api/v1/cart/items", json={"product_id": p3.id, "quantity": 2}, headers=customer_auth_headers)
    assert res.status_code == 200

    # 19.99 * 3 = 59.97
    # 49.95 * 7 = 349.65
    # 109.90 * 2 = 219.80
    # Expected subtotal = 629.42
    data = res.json()
    assert data["item_count"] == 3
    assert data["total_quantity"] == 12
    assert Decimal(data["subtotal"]) == Decimal("629.42")

