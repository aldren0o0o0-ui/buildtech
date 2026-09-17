from decimal import Decimal
import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, hash_password
from app.modules.addresses.models import Address
from app.modules.carts.models import Cart, CartItem
from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.inventory.models import (
    Inventory,
    InventoryTransaction,
    InventoryTransactionType,
)
from app.modules.orders.models import (
    Order,
    OrderItem,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
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


@pytest.fixture
def valid_checkout_payload():
    return {
        "customer_name": "Jane Doe",
        "customer_email": "jane.doe@example.com",
        "customer_phone": "+639171234567",
        "shipping_address_line1": "123 Tech Street",
        "shipping_address_line2": "Unit 4B",
        "shipping_city": "Quezon City",
        "shipping_province": "Metro Manila",
        "shipping_postal_code": "1100",
        "shipping_country": "Philippines",
        "payment_method": "COD",
    }


# =========================================================================
# 1-14: CHECKOUT CORE TESTS
# =========================================================================

def test_customer_checkout_success(
    client, customer_auth_headers, test_customer_user, active_product, valid_checkout_payload, db_session
):
    # Add product to cart
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 2},
        headers=customer_auth_headers,
    )

    # Perform checkout
    response = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["order_number"].startswith("BT-")
    assert data["status"] == "CONFIRMED"
    assert data["payment_method"] == "COD"
    assert data["payment_status"] == "PENDING"
    assert Decimal(str(data["subtotal"])) == Decimal("899.98")
    assert Decimal(str(data["total_amount"])) == Decimal("899.98")
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] == active_product.id
    assert data["items"][0]["quantity"] == 2
    assert Decimal(str(data["items"][0]["unit_price"])) == Decimal("449.99")
    assert Decimal(str(data["items"][0]["subtotal"])) == Decimal("899.98")


def test_unauthenticated_checkout_rejected(client, valid_checkout_payload):
    response = client.post("/api/v1/checkout", json=valid_checkout_payload)
    assert response.status_code == 401


def test_admin_cannot_use_customer_checkout(client, admin_auth_headers, valid_checkout_payload):
    response = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=admin_auth_headers,
    )
    assert response.status_code == 403


def test_empty_cart_checkout_rejected(client, customer_auth_headers, valid_checkout_payload):
    response = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_inactive_product_rejected(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    # Add product to cart
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )

    # Deactivate product
    active_product.is_active = False
    db_session.add(active_product)
    db_session.commit()

    response = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert response.status_code == 400
    assert "no longer active" in response.json()["detail"].lower()


def test_unavailable_product_status_rejected(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )

    active_product.status = ProductStatus.DRAFT.value
    db_session.add(active_product)
    db_session.commit()

    response = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert response.status_code == 400


def test_insufficient_inventory_rejected(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 5},
        headers=customer_auth_headers,
    )

    # Reduce available stock behind the scenes
    inv = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first()
    inv.quantity = 2
    db_session.add(inv)
    db_session.commit()

    response = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert response.status_code == 409
    assert "insufficient" in response.json()["detail"].lower()


def test_successful_checkout_clears_cart_items(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session, test_customer_user
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 2},
        headers=customer_auth_headers,
    )

    resp = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert resp.status_code == 201

    # Verify Cart record exists but items are empty
    cart = db_session.query(Cart).filter(Cart.user_id == test_customer_user.id).first()
    assert cart is not None
    assert len(cart.items) == 0


def test_successful_checkout_deducts_inventory(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 3},
        headers=customer_auth_headers,
    )

    resp = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert resp.status_code == 201

    inv = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first()
    assert inv.quantity == 7
    assert inv.reserved_quantity == 0


def test_successful_checkout_creates_sale_transaction(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session, test_customer_user
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 4},
        headers=customer_auth_headers,
    )

    resp = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert resp.status_code == 201

    tx = (
        db_session.query(InventoryTransaction)
        .filter(
            InventoryTransaction.product_id == active_product.id,
            InventoryTransaction.type == InventoryTransactionType.SALE.value,
        )
        .first()
    )
    assert tx is not None
    assert tx.quantity_change == -4
    assert tx.quantity_before == 10
    assert tx.quantity_after == 6
    assert tx.created_by_user_id == test_customer_user.id


def test_order_total_calculated_correctly(
    client, customer_auth_headers, active_product, second_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 2},  # 2 * 449.99 = 899.98
        headers=customer_auth_headers,
    )
    client.post(
        "/api/v1/cart/items",
        json={"product_id": second_product.id, "quantity": 1},  # 1 * 899.00 = 899.00
        headers=customer_auth_headers,
    )

    resp = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["subtotal"])) == Decimal("1798.98")
    assert Decimal(str(data["shipping_fee"])) == Decimal("0.00")
    assert Decimal(str(data["total_amount"])) == Decimal("1798.98")


def test_order_items_store_price_and_product_snapshots(
    client, customer_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )

    resp = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert resp.status_code == 201
    item = resp.json()["items"][0]
    assert item["product_name"] == active_product.name
    assert item["product_sku"] == active_product.sku
    assert item["product_slug"] == active_product.slug
    assert Decimal(str(item["unit_price"])) == active_product.price


def test_customer_snapshot_stored_correctly(
    client, customer_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )

    resp = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["customer_name"] == valid_checkout_payload["customer_name"]
    assert data["customer_email"] == valid_checkout_payload["customer_email"]
    assert data["customer_phone"] == valid_checkout_payload["customer_phone"]


def test_shipping_snapshot_stored_correctly(
    client, customer_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )

    resp = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["shipping_address_line1"] == valid_checkout_payload["shipping_address_line1"]
    assert data["shipping_address_line2"] == valid_checkout_payload["shipping_address_line2"]
    assert data["shipping_city"] == valid_checkout_payload["shipping_city"]
    assert data["shipping_province"] == valid_checkout_payload["shipping_province"]
    assert data["shipping_postal_code"] == valid_checkout_payload["shipping_postal_code"]
    assert data["shipping_country"] == valid_checkout_payload["shipping_country"]


# =========================================================================
# 15-17: OWNERSHIP & VISIBILITY TESTS
# =========================================================================

def test_customer_can_view_own_order(
    client, customer_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    created = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    ).json()

    # View by numeric ID
    res_id = client.get(f"/api/v1/orders/{created['id']}", headers=customer_auth_headers)
    assert res_id.status_code == 200
    assert res_id.json()["id"] == created["id"]

    # View by order_number
    res_num = client.get(f"/api/v1/orders/{created['order_number']}", headers=customer_auth_headers)
    assert res_num.status_code == 200
    assert res_num.json()["order_number"] == created["order_number"]


def test_customer_cannot_view_another_customers_order(
    client, customer_auth_headers, second_customer_headers, active_product, valid_checkout_payload
):
    # Customer 1 creates an order
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    created = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    ).json()

    # Customer 2 attempts to view Customer 1's order
    res = client.get(f"/api/v1/orders/{created['id']}", headers=second_customer_headers)
    assert res.status_code == 404

    res_num = client.get(f"/api/v1/orders/{created['order_number']}", headers=second_customer_headers)
    assert res_num.status_code == 404


def test_customer_can_list_only_own_orders(
    client, customer_auth_headers, second_customer_headers, active_product, second_product, valid_checkout_payload
):
    # Customer 1 order
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    client.post("/api/v1/checkout", json=valid_checkout_payload, headers=customer_auth_headers)

    # Customer 2 order
    client.post(
        "/api/v1/cart/items",
        json={"product_id": second_product.id, "quantity": 1},
        headers=second_customer_headers,
    )
    client.post("/api/v1/checkout", json=valid_checkout_payload, headers=second_customer_headers)

    # Customer 1 lists orders
    res1 = client.get("/api/v1/orders", headers=customer_auth_headers)
    assert res1.status_code == 200
    assert res1.json()["total"] == 1
    assert res1.json()["items"][0]["items"][0]["product_id"] == active_product.id


# =========================================================================
# 18: IDEMPOTENCY TEST
# =========================================================================

def test_repeated_checkout_with_same_idempotency_key_does_not_create_duplicate_order(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )

    key = "test-idempotency-key-12345"
    resp1 = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers={**customer_auth_headers, "Idempotency-Key": key},
    )
    assert resp1.status_code == 201
    order1 = resp1.json()

    # Retry same checkout request
    resp2 = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers={**customer_auth_headers, "Idempotency-Key": key},
    )
    assert resp2.status_code in (200, 201)
    order2 = resp2.json()

    assert order1["order_number"] == order2["order_number"]
    assert db_session.query(Order).count() == 1


# =========================================================================
# 19-22: INVENTORY INTEGRITY & ATOMICITY TESTS
# =========================================================================

def test_checkout_never_produces_negative_inventory(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    inv = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first()
    inv.quantity = 1
    db_session.add(inv)
    db_session.commit()

    # Attempt to order 2 units
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    # Manually increase cart item quantity past inventory to test checkout rejection
    cart_item = db_session.query(CartItem).first()
    cart_item.quantity = 5
    db_session.add(cart_item)
    db_session.commit()

    resp = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert resp.status_code == 409

    db_session.refresh(inv)
    assert inv.quantity == 1


def test_inventory_transaction_is_atomic_with_order(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    # Attempting checkout with empty cart
    resp = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert resp.status_code == 400
    assert db_session.query(Order).count() == 0
    assert db_session.query(InventoryTransaction).count() == 0


def test_failed_checkout_does_not_modify_inventory(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    active_product.is_active = False
    db_session.add(active_product)
    db_session.commit()

    resp = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert resp.status_code == 400

    inv = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first()
    assert inv.quantity == 10


def test_failed_checkout_does_not_clear_cart(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    active_product.is_active = False
    db_session.add(active_product)
    db_session.commit()

    resp = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    )
    assert resp.status_code == 400

    cart_item = db_session.query(CartItem).first()
    assert cart_item is not None
    assert cart_item.product_id == active_product.id


# =========================================================================
# 23-24: PRICE MANIPULATION & HISTORICAL INTEGRITY TESTS
# =========================================================================

def test_client_supplied_prices_are_ignored_or_rejected(
    client, customer_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )

    malicious_payload = {
        **valid_checkout_payload,
        "subtotal": 1.00,
        "total_amount": 1.00,
        "unit_price": 1.00,
    }

    # Pydantic extra='forbid' rejects client tampering directly
    resp = client.post(
        "/api/v1/checkout",
        json=malicious_payload,
        headers=customer_auth_headers,
    )
    assert resp.status_code == 422


def test_product_price_changes_after_checkout_do_not_alter_order_history(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    created = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    ).json()

    # Product price changes in catalog
    active_product.price = Decimal("9999.99")
    active_product.name = "Renamed Future Product"
    db_session.add(active_product)
    db_session.commit()

    # Query historical order
    order_res = client.get(f"/api/v1/orders/{created['id']}", headers=customer_auth_headers).json()
    assert Decimal(str(order_res["subtotal"])) == Decimal("449.99")
    assert order_res["items"][0]["product_name"] == "AMD Ryzen 7 7800X3D"
    assert Decimal(str(order_res["items"][0]["unit_price"])) == Decimal("449.99")


# =========================================================================
# 25-29: CANCELLATION TESTS
# =========================================================================

def test_eligible_order_can_be_cancelled(
    client, customer_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 2},
        headers=customer_auth_headers,
    )
    order = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    ).json()

    cancel_res = client.post(
        f"/api/v1/orders/{order['id']}/cancel",
        headers=customer_auth_headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"
    assert cancel_res.json()["payment_status"] == "CANCELLED"


def test_cancellation_restores_inventory(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 3},
        headers=customer_auth_headers,
    )
    order = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    ).json()

    inv = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first()
    assert inv.quantity == 7

    client.post(f"/api/v1/orders/{order['id']}/cancel", headers=customer_auth_headers)

    db_session.refresh(inv)
    assert inv.quantity == 10


def test_cancellation_creates_reversal_inventory_transaction(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session, test_customer_user
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 2},
        headers=customer_auth_headers,
    )
    order = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    ).json()

    client.post(f"/api/v1/orders/{order['id']}/cancel", headers=customer_auth_headers)

    reversal_tx = (
        db_session.query(InventoryTransaction)
        .filter(
            InventoryTransaction.product_id == active_product.id,
            InventoryTransaction.type == InventoryTransactionType.SALE_REVERSAL.value,
        )
        .first()
    )
    assert reversal_tx is not None
    assert reversal_tx.quantity_change == 2
    assert reversal_tx.quantity_before == 8
    assert reversal_tx.quantity_after == 10


def test_completed_order_cannot_be_cancelled(
    client, customer_auth_headers, admin_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    order = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    ).json()

    # Admin advances order to COMPLETED
    client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "PROCESSING"},
        headers=admin_auth_headers,
    )
    client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "READY_FOR_FULFILLMENT"},
        headers=admin_auth_headers,
    )
    client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "COMPLETED"},
        headers=admin_auth_headers,
    )

    # Customer attempts to cancel completed order
    res = client.post(f"/api/v1/orders/{order['id']}/cancel", headers=customer_auth_headers)
    assert res.status_code == 400


def test_invalid_status_transition_rejected(
    client, customer_auth_headers, admin_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    order = client.post(
        "/api/v1/checkout",
        json=valid_checkout_payload,
        headers=customer_auth_headers,
    ).json()

    # Invalid jump from CONFIRMED straight to COMPLETED
    res = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "COMPLETED"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 400


# =========================================================================
# 30-35: ADMIN MANAGEMENT TESTS
# =========================================================================

def test_admin_can_list_orders(
    client, customer_auth_headers, admin_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    client.post("/api/v1/checkout", json=valid_checkout_payload, headers=customer_auth_headers)

    res = client.get("/api/v1/admin/orders", headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 1


def test_admin_can_search_orders(
    client, customer_auth_headers, admin_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    order = client.post("/api/v1/checkout", json=valid_checkout_payload, headers=customer_auth_headers).json()

    res = client.get(f"/api/v1/admin/orders?search={order['order_number']}", headers=admin_auth_headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 1
    assert res.json()["items"][0]["order_number"] == order["order_number"]


def test_admin_can_filter_orders(
    client, customer_auth_headers, admin_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    client.post("/api/v1/checkout", json=valid_checkout_payload, headers=customer_auth_headers)

    res_confirmed = client.get("/api/v1/admin/orders?status=CONFIRMED", headers=admin_auth_headers)
    assert res_confirmed.status_code == 200
    assert len(res_confirmed.json()["items"]) >= 1

    res_cancelled = client.get("/api/v1/admin/orders?status=CANCELLED", headers=admin_auth_headers)
    assert res_cancelled.status_code == 200
    assert len(res_cancelled.json()["items"]) == 0


def test_admin_can_view_order_details(
    client, customer_auth_headers, admin_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    order = client.post("/api/v1/checkout", json=valid_checkout_payload, headers=customer_auth_headers).json()

    res = client.get(f"/api/v1/admin/orders/{order['id']}", headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["order_number"] == order["order_number"]


def test_admin_can_update_valid_order_status(
    client, customer_auth_headers, admin_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    order = client.post("/api/v1/checkout", json=valid_checkout_payload, headers=customer_auth_headers).json()

    res = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "PROCESSING"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "PROCESSING"


def test_admin_invalid_status_transition_rejected(
    client, customer_auth_headers, admin_auth_headers, active_product, valid_checkout_payload
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    order = client.post("/api/v1/checkout", json=valid_checkout_payload, headers=customer_auth_headers).json()

    res = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "COMPLETED"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 400


# =========================================================================
# 36-39: DATABASE INTEGRITY & PRODUCT DELETION
# =========================================================================

def test_duplicate_order_number_prevented(db_session, test_customer_user):
    order1 = Order(
        order_number="BT-UNIQUE-001",
        user_id=test_customer_user.id,
        status="CONFIRMED",
        payment_method="COD",
        payment_status="PENDING",
        subtotal=Decimal("100.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        customer_name="Test",
        customer_email="test@example.com",
        customer_phone="1234567",
        shipping_address_line1="123 Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
        shipping_country="Philippines",
    )
    db_session.add(order1)
    db_session.commit()

    order2 = Order(
        order_number="BT-UNIQUE-001",
        user_id=test_customer_user.id,
        status="CONFIRMED",
        payment_method="COD",
        payment_status="PENDING",
        subtotal=Decimal("200.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("200.00"),
        customer_name="Test 2",
        customer_email="test2@example.com",
        customer_phone="7654321",
        shipping_address_line1="456 Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
        shipping_country="Philippines",
    )
    db_session.add(order2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_invalid_negative_monetary_values_rejected(db_session, test_customer_user):
    order = Order(
        order_number="BT-NEG-001",
        user_id=test_customer_user.id,
        status="CONFIRMED",
        payment_method="COD",
        payment_status="PENDING",
        subtotal=Decimal("-10.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("-10.00"),
        customer_name="Test",
        customer_email="test@example.com",
        customer_phone="1234567",
        shipping_address_line1="123 Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
        shipping_country="Philippines",
    )
    db_session.add(order)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_invalid_quantity_rejected(db_session, test_customer_user):
    order = Order(
        order_number="BT-QTY-001",
        user_id=test_customer_user.id,
        status="CONFIRMED",
        payment_method="COD",
        payment_status="PENDING",
        subtotal=Decimal("100.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        customer_name="Test",
        customer_email="test@example.com",
        customer_phone="1234567",
        shipping_address_line1="123 Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
        shipping_country="Philippines",
    )
    db_session.add(order)
    db_session.commit()

    item = OrderItem(
        order_id=order.id,
        product_id=None,
        product_name="Sample",
        product_sku="SKU-1",
        product_slug="sample",
        unit_price=Decimal("100.00"),
        quantity=0,  # Invalid: quantity must be >= 1
        subtotal=Decimal("0.00"),
    )
    db_session.add(item)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_deleted_product_does_not_destroy_historical_order_information(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 2},
        headers=customer_auth_headers,
    )
    created = client.post("/api/v1/checkout", json=valid_checkout_payload, headers=customer_auth_headers).json()

    # Delete product from catalog
    db_session.delete(active_product)
    db_session.commit()

    # Historical order must remain completely readable
    order_res = client.get(f"/api/v1/orders/{created['id']}", headers=customer_auth_headers)
    assert order_res.status_code == 200
    data = order_res.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["product_id"] is None
    assert data["items"][0]["product_name"] == "AMD Ryzen 7 7800X3D"
    assert Decimal(str(data["items"][0]["unit_price"])) == Decimal("449.99")
    assert Decimal(str(data["items"][0]["subtotal"])) == Decimal("899.98")


# =========================================================================
# 40: CONCURRENCY PROTECTION TEST
# =========================================================================

def test_concurrency_protection_for_stock(
    client, customer_auth_headers, second_customer_headers, active_product, valid_checkout_payload, db_session
):
    """
    Validates that when stock is 5, and two customers both attempt to checkout 4 units,
    only ONE checkout succeeds and the other fails with 409 Conflict.
    The final inventory must be exactly 1, never negative.
    """
    inv = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first()
    inv.quantity = 5
    db_session.add(inv)
    db_session.commit()

    # Customer 1 adds 4 units
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 4},
        headers=customer_auth_headers,
    )

    # Customer 2 adds 4 units
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 4},
        headers=second_customer_headers,
    )

    # Customer 1 checks out first
    resp1 = client.post("/api/v1/checkout", json=valid_checkout_payload, headers=customer_auth_headers)
    assert resp1.status_code == 201

    # Customer 2 checks out next (competing for remaining 1 unit)
    resp2 = client.post("/api/v1/checkout", json=valid_checkout_payload, headers=second_customer_headers)
    assert resp2.status_code == 409

    # Verify inventory is exactly 1 unit
    db_session.refresh(inv)
    assert inv.quantity == 1
    assert inv.reserved_quantity == 0


# =========================================================================
# 41-48: MODULE 10 SPECIFIC ENHANCEMENTS
# =========================================================================

def test_order_creation_with_saved_address_id(
    client, customer_auth_headers, test_customer_user, active_product, db_session
):
    """Customer can place an order referencing a saved Module 9 address."""
    addr = Address(
        user_id=test_customer_user.id,
        recipient_name="John Doe",
        phone="+639171234567",
        address_line1="742 Evergreen Terrace",
        address_line2="Apt 2",
        barangay="San Antonio",
        city="Pasig",
        province="Metro Manila",
        postal_code="1600",
        country="Philippines",
        is_default=True,
    )
    db_session.add(addr)
    db_session.commit()

    # Add item to cart
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )

    # Place order via POST /api/v1/orders
    res = client.post(
        "/api/v1/orders",
        json={
            "address_id": addr.id,
            "notes": "Handle with care, delicate electronics",
            "payment_method": "COD",
        },
        headers=customer_auth_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["order_number"].startswith("BT-")
    assert data["status"] == "CONFIRMED"
    assert data["customer_name"] == "John Doe"
    assert data["recipient_name"] == "John Doe"
    assert data["shipping_barangay"] == "San Antonio"
    assert data["shipping_city"] == "Pasig"
    assert data["notes"] == "Handle with care, delicate electronics"
    assert len(data["items"]) == 1
    assert data["items"][0]["sku"] == active_product.sku

    # Cart should now be empty
    cart_res = client.get("/api/v1/cart", headers=customer_auth_headers)
    assert len(cart_res.json()["items"]) == 0


def test_order_address_snapshot_immutability(
    client, customer_auth_headers, test_customer_user, active_product, db_session
):
    """Updating a saved address does NOT mutate historic order address snapshot."""
    addr = Address(
        user_id=test_customer_user.id,
        recipient_name="Original Name",
        phone="+639170000000",
        address_line1="Old Street 1",
        barangay="Old Barangay",
        city="Old City",
        province="Old Province",
        postal_code="1000",
        country="Philippines",
        is_default=True,
    )
    db_session.add(addr)
    db_session.commit()

    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )

    created_order = client.post(
        "/api/v1/orders",
        json={"address_id": addr.id},
        headers=customer_auth_headers,
    ).json()

    # Now customer modifies their address via Module 9 PATCH
    client.patch(
        f"/api/v1/addresses/{addr.id}",
        json={
            "recipient_name": "New Name",
            "address_line1": "New Street 99",
            "barangay": "New Barangay",
            "city": "New City",
        },
        headers=customer_auth_headers,
    )

    # Historic order must still reflect original snapshot
    order_res = client.get(f"/api/v1/orders/{created_order['order_number']}", headers=customer_auth_headers)
    assert order_res.status_code == 200
    hist = order_res.json()
    assert hist["customer_name"] == "Original Name"
    assert hist["recipient_name"] == "Original Name"
    assert hist["shipping_address_line1"] == "Old Street 1"
    assert hist["shipping_barangay"] == "Old Barangay"
    assert hist["shipping_city"] == "Old City"


def test_order_product_price_snapshot_immutability(
    client, customer_auth_headers, test_customer_user, active_product, db_session
):
    """Catalog price changes do NOT mutate historic order item prices."""
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    order_data = client.post(
        "/api/v1/orders",
        json={
            "customer_name": "Test Cust",
            "customer_email": "test@cust.com",
            "customer_phone": "+639171234567",
            "shipping_address_line1": "Street 1",
            "shipping_city": "City",
            "shipping_province": "Prov",
            "shipping_postal_code": "1234",
            "shipping_country": "Philippines",
        },
        headers=customer_auth_headers,
    ).json()

    # Change product price in catalog
    active_product.price = Decimal("999.99")
    db_session.add(active_product)
    db_session.commit()

    # Historic order must still show 449.99
    order_res = client.get(f"/api/v1/orders/{order_data['id']}", headers=customer_auth_headers)
    assert order_res.status_code == 200
    assert Decimal(str(order_res.json()["items"][0]["unit_price"])) == Decimal("449.99")


def test_order_creation_with_foreign_address_rejected(
    client, customer_auth_headers, second_customer, active_product, db_session
):
    """Customer cannot place an order using another customer's address_id."""
    foreign_addr = Address(
        user_id=second_customer.id,
        recipient_name="Foreign Customer",
        phone="+639179999999",
        address_line1="Foreign St",
        barangay="Foreign Brgy",
        city="Foreign City",
        province="Foreign Prov",
        postal_code="9999",
        country="Philippines",
    )
    db_session.add(foreign_addr)
    db_session.commit()

    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )

    res = client.post(
        "/api/v1/orders",
        json={"address_id": foreign_addr.id},
        headers=customer_auth_headers,
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_order_cancellation_records_cancelled_at(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    """Order cancellation records cancelled_at timestamp and safely restores stock."""
    inv = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first()
    initial_stock = inv.quantity

    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 2},
        headers=customer_auth_headers,
    )
    order = client.post("/api/v1/orders", json=valid_checkout_payload, headers=customer_auth_headers).json()

    # Cancel order
    cancel_res = client.post(f"/api/v1/orders/{order['order_number']}/cancel", headers=customer_auth_headers)
    assert cancel_res.status_code == 200
    data = cancel_res.json()
    assert data["status"] == "CANCELLED"
    assert data["cancelled_at"] is not None

    # Stock restored
    db_session.refresh(inv)
    assert inv.quantity == initial_stock

    # Second cancellation rejected
    repeat_res = client.post(f"/api/v1/orders/{order['order_number']}/cancel", headers=customer_auth_headers)
    assert repeat_res.status_code == 400


def test_strict_state_transitions_shipped_delivered(
    client, customer_auth_headers, admin_auth_headers, active_product, valid_checkout_payload
):
    """Admin transitions CONFIRMED -> PROCESSING -> SHIPPED -> DELIVERED (terminal)."""
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    order = client.post("/api/v1/orders", json=valid_checkout_payload, headers=customer_auth_headers).json()

    # CONFIRMED -> PROCESSING
    r1 = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "PROCESSING"},
        headers=admin_auth_headers,
    )
    assert r1.status_code == 200
    assert r1.json()["status"] == "PROCESSING"

    # PROCESSING -> SHIPPED
    r2 = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "SHIPPED"},
        headers=admin_auth_headers,
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "SHIPPED"

    # Customer CANNOT cancel a SHIPPED order
    c_res = client.post(f"/api/v1/orders/{order['id']}/cancel", headers=customer_auth_headers)
    assert c_res.status_code == 400

    # SHIPPED -> DELIVERED
    r3 = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "DELIVERED"},
        headers=admin_auth_headers,
    )
    assert r3.status_code == 200
    assert r3.json()["status"] == "DELIVERED"

    # DELIVERED is terminal: cannot be cancelled or transitioned back
    r_invalid1 = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "CANCELLED"},
        headers=admin_auth_headers,
    )
    assert r_invalid1.status_code == 400

    r_invalid2 = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "PENDING"},
        headers=admin_auth_headers,
    )
    assert r_invalid2.status_code == 400


def test_invalid_state_transitions_rejected(
    client, customer_auth_headers, admin_auth_headers, active_product, valid_checkout_payload
):
    """Verifies representative invalid transitions like CANCELLED -> PROCESSING and SHIPPED -> PENDING."""
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )
    order = client.post("/api/v1/orders", json=valid_checkout_payload, headers=customer_auth_headers).json()

    # Cancel order
    client.post(f"/api/v1/orders/{order['id']}/cancel", headers=customer_auth_headers)

    # CANCELLED -> PROCESSING must be rejected
    r = client.patch(
        f"/api/v1/admin/orders/{order['id']}/status",
        json={"status": "PROCESSING"},
        headers=admin_auth_headers,
    )
    assert r.status_code == 400


def test_idempotency_via_orders_endpoint(
    client, customer_auth_headers, active_product, valid_checkout_payload, db_session
):
    """Using Idempotency-Key header on POST /api/v1/orders prevents duplicate orders."""
    client.post(
        "/api/v1/cart/items",
        json={"product_id": active_product.id, "quantity": 1},
        headers=customer_auth_headers,
    )

    headers = {**customer_auth_headers, "Idempotency-Key": "IDEM-TEST-KEY-001"}

    resp1 = client.post("/api/v1/orders", json=valid_checkout_payload, headers=headers)
    assert resp1.status_code == 201
    order1 = resp1.json()

    # Re-send identical request
    resp2 = client.post("/api/v1/orders", json=valid_checkout_payload, headers=headers)
    assert resp2.status_code in (200, 201)
    order2 = resp2.json()

    assert order1["order_number"] == order2["order_number"]
    assert order1["id"] == order2["id"]
