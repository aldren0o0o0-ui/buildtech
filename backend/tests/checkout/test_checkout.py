from decimal import Decimal
import pytest

from app.core.security import create_access_token, hash_password
from app.modules.addresses.models import Address
from app.modules.carts.models import Cart, CartItem
from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.inventory.models import (
    Inventory,
    InventoryTransaction,
)
from app.modules.orders.models import Order, OrderItem
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


@pytest.fixture
def customer_address(db_session, test_customer_user):
    address = Address(
        user_id=test_customer_user.id,
        label="Home",
        recipient_name="Customer One",
        phone="09171234567",
        address_line1="123 Mabini St",
        barangay="San Antonio",
        city="Pasig",
        province="Metro Manila",
        postal_code="1600",
        country="Philippines",
        is_default=True,
    )
    db_session.add(address)
    db_session.commit()
    db_session.refresh(address)
    return address


@pytest.fixture
def second_customer_address(db_session, second_customer_user):
    address = Address(
        user_id=second_customer_user.id,
        label="Home",
        recipient_name="Customer Two",
        phone="09179876543",
        address_line1="456 Quezon Ave",
        barangay="West Triangle",
        city="Quezon City",
        province="Metro Manila",
        postal_code="1104",
        country="Philippines",
        is_default=True,
    )
    db_session.add(address)
    db_session.commit()
    db_session.refresh(address)
    return address


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
    )
    db_session.add(inv)
    db_session.commit()
    return prod


@pytest.fixture
def second_product(db_session, test_category, test_brand):
    prod = Product(
        sku="GPU-RTX-4080-SUPER",
        name="NVIDIA GeForce RTX 4080 Super",
        slug="nvidia-geforce-rtx-4080-super",
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
    )
    db_session.add(inv)
    db_session.commit()
    return prod


# =========================================================================
# 1. Basic Checkout Validation Flow
# =========================================================================

def test_validate_checkout_empty_cart_fails(client, customer_auth_headers, customer_address):
    """Empty cart returns valid=False and EMPTY_CART issue."""
    payload = {"address_id": customer_address.id}
    res = client.post("/api/v1/checkout/validate", json=payload, headers=customer_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is False
    assert len(data["issues"]) == 1
    assert data["issues"][0]["code"] == "EMPTY_CART"
    assert data["items"] == []


def test_validate_checkout_success(
    client,
    customer_auth_headers,
    customer_address,
    active_product,
    second_product,
):
    """Valid cart and valid address returns valid=True with authoritative preview."""
    # Add products to cart
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"product_id": second_product.id, "quantity": 1}, headers=customer_auth_headers)

    payload = {"address_id": customer_address.id}
    res = client.post("/api/v1/checkout/validate", json=payload, headers=customer_auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["valid"] is True
    assert len(data["issues"]) == 0
    assert len(data["items"]) == 2

    # Address snapshot preview
    assert data["address"]["id"] == customer_address.id
    assert data["address"]["recipient_name"] == customer_address.recipient_name

    # Check totals: 449.99 * 2 = 899.98; 999.00 * 1 = 999.00; Subtotal = 1898.98
    expected_subtotal = Decimal("449.99") * 2 + Decimal("999.00")
    assert Decimal(data["subtotal"]) == expected_subtotal
    assert Decimal(data["shipping_fee"]) == Decimal("0.00")
    assert Decimal(data["tax"]) == Decimal("0.00")
    assert Decimal(data["total"]) == expected_subtotal


# =========================================================================
# 2. Customer Address Isolation
# =========================================================================

def test_validate_checkout_address_not_found(client, customer_auth_headers, active_product):
    """Non-existent address ID returns 404 Not Found."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 1}, headers=customer_auth_headers)
    res = client.post("/api/v1/checkout/validate", json={"address_id": 99999}, headers=customer_auth_headers)
    assert res.status_code == 404
    assert "address not found" in res.json()["detail"].lower()


def test_validate_checkout_customer_cannot_use_other_customer_address(
    client,
    customer_auth_headers,
    second_customer_address,
    active_product,
):
    """Customer A cannot validate checkout using Customer B's address (returns 404)."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 1}, headers=customer_auth_headers)
    res = client.post(
        "/api/v1/checkout/validate",
        json={"address_id": second_customer_address.id},
        headers=customer_auth_headers,
    )
    assert res.status_code == 404
    assert "address not found" in res.json()["detail"].lower()


# =========================================================================
# 3. Product & Inventory Availability Scenarios
# =========================================================================

def test_validate_checkout_inactive_product_reported(
    client,
    customer_auth_headers,
    customer_address,
    active_product,
    db_session,
):
    """If product becomes inactive after being added to cart, validation reports PRODUCT_UNAVAILABLE."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 1}, headers=customer_auth_headers)

    # Deactivate product in catalog
    active_product.is_active = False
    db_session.add(active_product)
    db_session.commit()

    res = client.post(
        "/api/v1/checkout/validate",
        json={"address_id": customer_address.id},
        headers=customer_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is False
    assert len(data["issues"]) == 1
    assert data["issues"][0]["code"] == "PRODUCT_UNAVAILABLE"
    assert data["items"][0]["status"] == "PRODUCT_UNAVAILABLE"


def test_validate_checkout_draft_product_reported(
    client,
    customer_auth_headers,
    customer_address,
    active_product,
    db_session,
):
    """If product status changes to DRAFT, validation reports PRODUCT_UNAVAILABLE."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 1}, headers=customer_auth_headers)

    active_product.status = ProductStatus.DRAFT.value
    db_session.add(active_product)
    db_session.commit()

    res = client.post(
        "/api/v1/checkout/validate",
        json={"address_id": customer_address.id},
        headers=customer_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is False
    assert data["issues"][0]["code"] == "PRODUCT_UNAVAILABLE"


def test_validate_checkout_out_of_stock_reported(
    client,
    customer_auth_headers,
    customer_address,
    active_product,
    db_session,
):
    """If product inventory drops to 0, validation reports OUT_OF_STOCK."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)

    # Reduce stock to 0
    inv = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first()
    inv.quantity = 0
    db_session.add(inv)
    db_session.commit()

    res = client.post(
        "/api/v1/checkout/validate",
        json={"address_id": customer_address.id},
        headers=customer_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is False
    assert len(data["issues"]) == 1
    assert data["issues"][0]["code"] == "OUT_OF_STOCK"
    assert data["issues"][0]["available_quantity"] == 0
    assert data["items"][0]["status"] == "OUT_OF_STOCK"


def test_validate_checkout_insufficient_stock_reported(
    client,
    customer_auth_headers,
    customer_address,
    active_product,
    db_session,
):
    """If stock drops below requested quantity, validation reports INSUFFICIENT_STOCK."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 5}, headers=customer_auth_headers)

    # Stock drops from 10 to 3
    inv = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first()
    inv.quantity = 3
    db_session.add(inv)
    db_session.commit()

    res = client.post(
        "/api/v1/checkout/validate",
        json={"address_id": customer_address.id},
        headers=customer_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is False
    assert len(data["issues"]) == 1
    assert data["issues"][0]["code"] == "INSUFFICIENT_STOCK"
    assert data["issues"][0]["requested_quantity"] == 5
    assert data["issues"][0]["available_quantity"] == 3


def test_validate_checkout_authoritative_price_used(
    client,
    customer_auth_headers,
    customer_address,
    active_product,
    db_session,
):
    """Checkout validator dynamically uses authoritative catalog price if price changed after adding to cart."""
    # Added at 449.99
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 1}, headers=customer_auth_headers)

    # Admin updates price to 499.00
    active_product.price = Decimal("499.00")
    db_session.add(active_product)
    db_session.commit()

    res = client.post(
        "/api/v1/checkout/validate",
        json={"address_id": customer_address.id},
        headers=customer_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert Decimal(data["items"][0]["unit_price"]) == Decimal("499.00")
    assert Decimal(data["subtotal"]) == Decimal("499.00")


def test_validate_checkout_decimal_precision_multi_item(
    client,
    customer_auth_headers,
    customer_address,
    test_category,
    test_brand,
    db_session,
):
    """Validates precise multi-item Decimal calculations with zero floating-point inaccuracies."""
    p1 = Product(sku="ITEM-A", name="Item A", slug="item-a", category_id=test_category.id, brand_id=test_brand.id, price=Decimal("19.99"), status=ProductStatus.ACTIVE.value, is_active=True)
    p2 = Product(sku="ITEM-B", name="Item B", slug="item-b", category_id=test_category.id, brand_id=test_brand.id, price=Decimal("49.95"), status=ProductStatus.ACTIVE.value, is_active=True)
    db_session.add_all([p1, p2])
    db_session.flush()

    db_session.add_all([
        Inventory(product_id=p1.id, quantity=10, reserved_quantity=0),
        Inventory(product_id=p2.id, quantity=10, reserved_quantity=0),
    ])
    db_session.commit()

    client.post("/api/v1/cart/items", json={"product_id": p1.id, "quantity": 3}, headers=customer_auth_headers)
    client.post("/api/v1/cart/items", json={"product_id": p2.id, "quantity": 2}, headers=customer_auth_headers)

    res = client.post("/api/v1/checkout/validate", json={"address_id": customer_address.id}, headers=customer_auth_headers)
    assert res.status_code == 200
    data = res.json()

    # 19.99 * 3 = 59.97
    # 49.95 * 2 = 99.90
    # Subtotal = 159.87
    assert Decimal(data["subtotal"]) == Decimal("159.87")
    assert Decimal(data["total"]) == Decimal("159.87")


# =========================================================================
# 4. CRITICAL ARCHITECTURAL INVARIANT:
#    Validation does NOT mutate inventory, transactions, cart, or orders
# =========================================================================

def test_validate_checkout_does_not_mutate_inventory(
    client,
    customer_auth_headers,
    customer_address,
    active_product,
    db_session,
):
    """Verify strictly that checkout validation does not alter inventory or reserved_quantity."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 3}, headers=customer_auth_headers)

    inv_before = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first()
    qty_before = inv_before.quantity
    reserved_before = inv_before.reserved_quantity

    res = client.post("/api/v1/checkout/validate", json={"address_id": customer_address.id}, headers=customer_auth_headers)
    assert res.status_code == 200

    db_session.refresh(inv_before)
    assert inv_before.quantity == qty_before
    assert inv_before.reserved_quantity == reserved_before


def test_validate_checkout_does_not_create_inventory_transactions(
    client,
    customer_auth_headers,
    customer_address,
    active_product,
    db_session,
):
    """Verify strictly that checkout validation generates 0 inventory transactions."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 3}, headers=customer_auth_headers)

    tx_count_before = db_session.query(InventoryTransaction).count()

    res = client.post("/api/v1/checkout/validate", json={"address_id": customer_address.id}, headers=customer_auth_headers)
    assert res.status_code == 200

    tx_count_after = db_session.query(InventoryTransaction).count()
    assert tx_count_after == tx_count_before


def test_validate_checkout_does_not_clear_cart(
    client,
    customer_auth_headers,
    customer_address,
    active_product,
    db_session,
    test_customer_user,
):
    """Verify strictly that checkout validation preserves cart items."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)

    cart = db_session.query(Cart).filter(Cart.user_id == test_customer_user.id).first()
    items_count_before = len(cart.items)

    res = client.post("/api/v1/checkout/validate", json={"address_id": customer_address.id}, headers=customer_auth_headers)
    assert res.status_code == 200

    db_session.refresh(cart)
    assert len(cart.items) == items_count_before


def test_validate_checkout_does_not_create_orders(
    client,
    customer_auth_headers,
    customer_address,
    active_product,
    db_session,
):
    """Verify strictly that checkout validation does NOT create Order or OrderItem records."""
    client.post("/api/v1/cart/items", json={"product_id": active_product.id, "quantity": 2}, headers=customer_auth_headers)

    orders_count_before = db_session.query(Order).count()
    order_items_count_before = db_session.query(OrderItem).count()

    res = client.post("/api/v1/checkout/validate", json={"address_id": customer_address.id}, headers=customer_auth_headers)
    assert res.status_code == 200

    assert db_session.query(Order).count() == orders_count_before
    assert db_session.query(OrderItem).count() == order_items_count_before


# =========================================================================
# 5. Security & Authorization
# =========================================================================

def test_validate_checkout_unauthenticated_rejected(client, customer_address):
    """Unauthenticated users receive 401 Unauthorized."""
    res = client.post("/api/v1/checkout/validate", json={"address_id": customer_address.id})
    assert res.status_code == 401


def test_validate_checkout_admin_rejected(client, admin_auth_headers, customer_address):
    """Admin users receive 403 Forbidden."""
    res = client.post(
        "/api/v1/checkout/validate",
        json={"address_id": customer_address.id},
        headers=admin_auth_headers,
    )
    assert res.status_code == 403
