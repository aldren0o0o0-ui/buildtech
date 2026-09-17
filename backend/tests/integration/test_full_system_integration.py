from decimal import Decimal
from datetime import datetime, timezone
import pytest
from app.core.status import status
from app.core.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.modules.addresses.models import Address
from app.modules.carts.models import Cart, CartItem
from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.inventory.models import Inventory, InventoryTransaction, InventoryTransactionType
from app.modules.orders.models import Order, OrderItem, OrderStatus, PaymentMethod, PaymentStatus
from app.modules.payment.models import Payment
from app.modules.products.models import Product, ProductStatus
from app.modules.reviews.models import Review, ReviewStatus
from app.modules.users.models import User, UserRole
from app.modules.wishlist.models import Wishlist, WishlistItem


# ---------------------------------------------------------------------------
# Setup Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_setup(db_session):
    """
    Sets up two customers, one admin, and a baseline hardware catalog.
    """
    admin = User(
        email="sys_admin@buildtech.com",
        password_hash=hash_password("AdminPass123!"),
        first_name="System",
        last_name="Admin",
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    cust1 = User(
        email="alice@example.com",
        password_hash=hash_password("AlicePass123!"),
        first_name="Alice",
        last_name="Builder",
        role=UserRole.CUSTOMER.value,
        is_active=True,
    )
    cust2 = User(
        email="bob@example.com",
        password_hash=hash_password("BobPass123!"),
        first_name="Bob",
        last_name="Gamer",
        role=UserRole.CUSTOMER.value,
        is_active=True,
    )
    db_session.add_all([admin, cust1, cust2])
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(cust1)
    db_session.refresh(cust2)

    cat_gpu = Category(name="Graphics Cards", slug="graphics-cards", is_active=True)
    cat_cpu = Category(name="Processors", slug="processors", is_active=True)
    brand_nvidia = Brand(name="NVIDIA", slug="nvidia", is_active=True)
    brand_amd = Brand(name="AMD", slug="amd", is_active=True)
    db_session.add_all([cat_gpu, cat_cpu, brand_nvidia, brand_amd])
    db_session.commit()

    token_admin = create_access_token(subject=admin.id, role=admin.role)
    token_cust1 = create_access_token(subject=cust1.id, role=cust1.role)
    token_cust2 = create_access_token(subject=cust2.id, role=cust2.role)

    return {
        "admin": admin,
        "cust1": cust1,
        "cust2": cust2,
        "headers_admin": {"Authorization": f"Bearer {token_admin}"},
        "headers_cust1": {"Authorization": f"Bearer {token_cust1}"},
        "headers_cust2": {"Authorization": f"Bearer {token_cust2}"},
        "cat_gpu": cat_gpu,
        "cat_cpu": cat_cpu,
        "brand_nvidia": brand_nvidia,
        "brand_amd": brand_amd,
    }


# ---------------------------------------------------------------------------
# Phase 1 & 15: Cross-Module Authorization Matrix
# ---------------------------------------------------------------------------

def test_authorization_matrix_across_all_domains(client: TestClient, test_setup):
    headers_c1 = test_setup["headers_cust1"]
    headers_admin = test_setup["headers_admin"]

    # 1. Dashboard: Guest 401, Customer 403, Admin 200
    assert client.get("/api/v1/admin/dashboard").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get("/api/v1/admin/dashboard", headers=headers_c1).status_code == status.HTTP_403_FORBIDDEN
    assert client.get("/api/v1/admin/dashboard", headers=headers_admin).status_code == status.HTTP_200_OK

    # 2. Cart: Guest 401, Customer 200
    assert client.get("/api/v1/cart").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get("/api/v1/cart", headers=headers_c1).status_code == status.HTTP_200_OK

    # 3. Wishlist: Guest 401, Customer 200
    assert client.get("/api/v1/wishlist").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get("/api/v1/wishlist", headers=headers_c1).status_code == status.HTTP_200_OK

    # 4. Addresses: Guest 401, Customer 200
    assert client.get("/api/v1/addresses").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get("/api/v1/addresses", headers=headers_c1).status_code == status.HTTP_200_OK

    # 5. Orders: Guest 401, Customer 200
    assert client.get("/api/v1/orders").status_code == status.HTTP_401_UNAUTHORIZED
    assert client.get("/api/v1/orders", headers=headers_c1).status_code == status.HTTP_200_OK

    # 6. Admin Reviews: Customer 403, Admin 200
    assert client.get("/api/v1/admin/reviews", headers=headers_c1).status_code == status.HTTP_403_FORBIDDEN
    assert client.get("/api/v1/admin/reviews", headers=headers_admin).status_code == status.HTTP_200_OK

    # 7. Admin Orders: Customer 403, Admin 200
    assert client.get("/api/v1/admin/orders", headers=headers_c1).status_code == status.HTTP_403_FORBIDDEN
    assert client.get("/api/v1/admin/orders", headers=headers_admin).status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# Phase 3: Product -> Inventory -> Storefront Search & Filtering
# ---------------------------------------------------------------------------

def test_product_to_inventory_storefront_lifecycle(db_session, client: TestClient, test_setup):
    headers_admin = test_setup["headers_admin"]
    cat_gpu = test_setup["cat_gpu"]
    brand_nvidia = test_setup["brand_nvidia"]

    # 1. Admin creates product
    res = client.post(
        "/api/v1/products",
        json={
            "name": "GeForce RTX 4080 Super",
            "sku": "GPU-4080S",
            "price": "999.99",
            "category_id": cat_gpu.id,
            "brand_id": brand_nvidia.id,
            "description": "High-end Ada Lovelace GPU",
        },
        headers=headers_admin,
    )
    assert res.status_code == status.HTTP_201_CREATED
    product_id = res.json()["id"]

    # 2. Stock replenishment
    res = client.post(
        f"/api/v1/inventory/{product_id}/stock-in",
        json={
            "quantity": 10,
            "reason": "Initial stock shipment",
        },
        headers=headers_admin,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["quantity"] == 10
    assert res.json()["available_quantity"] == 10
    assert res.json()["availability_status"] == "IN_STOCK"

    # 3. Storefront search & filtering
    res = client.get("/api/v1/products?search=4080")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    items = data["items"] if isinstance(data, dict) and "items" in data else data
    assert len(items) == 1
    assert items[0]["id"] == product_id

    # 4. Out of stock transition
    res = client.post(
        f"/api/v1/inventory/{product_id}/adjust",
        json={
            "type": "ADJUSTMENT_OUT",
            "quantity": 10,
            "reason": "Damaged in warehouse",
        },
        headers=headers_admin,
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["available_quantity"] == 0
    assert res.json()["availability_status"] == "OUT_OF_STOCK"


# ---------------------------------------------------------------------------
# Phase 4: Wishlist -> Product Integration
# ---------------------------------------------------------------------------

def test_wishlist_lifecycle_and_cross_customer_isolation(db_session, client: TestClient, test_setup):
    headers_c1 = test_setup["headers_cust1"]
    headers_c2 = test_setup["headers_cust2"]
    cat = test_setup["cat_cpu"]
    brand = test_setup["brand_amd"]

    prod = Product(
        name="Ryzen 7 9800X3D",
        slug="ryzen-7-9800x3d",
        sku="CPU-9800X3D",
        price=Decimal("479.99"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    # Cust1 adds to wishlist
    res = client.post("/api/v1/wishlist/items", json={"product_id": prod.id}, headers=headers_c1)
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["item_count"] == 1
    wishlist_item_id = res.json()["items"][0]["id"]

    # Duplicate wishlist addition is idempotent / handled safely
    res_dup = client.post("/api/v1/wishlist/items", json={"product_id": prod.id}, headers=headers_c1)
    assert res_dup.status_code == status.HTTP_200_OK

    # Cust2 wishlist is empty (customer isolation)
    res_c2 = client.get("/api/v1/wishlist", headers=headers_c2)
    assert res_c2.status_code == status.HTTP_200_OK
    assert res_c2.json()["item_count"] == 0

    # Cust2 cannot delete Cust1's wishlist item
    res_del = client.delete(f"/api/v1/wishlist/items/{wishlist_item_id}", headers=headers_c2)
    # Deleting an item not in Cust2's wishlist returns 404
    assert res_del.status_code == status.HTTP_404_NOT_FOUND

    # Cust1 can delete their own item
    res_del_c1 = client.delete(f"/api/v1/wishlist/items/{wishlist_item_id}", headers=headers_c1)
    assert res_del_c1.status_code == status.HTTP_200_OK
    assert res_del_c1.json()["item_count"] == 0


# ---------------------------------------------------------------------------
# Phase 5: Cart Invariants -> Inventory Never Reserved by Cart
# ---------------------------------------------------------------------------

def test_cart_operations_never_mutate_inventory(db_session, client: TestClient, test_setup):
    headers_c1 = test_setup["headers_cust1"]
    cat = test_setup["cat_cpu"]
    brand = test_setup["brand_amd"]

    prod = Product(
        name="Ryzen 9 9950X",
        slug="ryzen-9-9950x",
        sku="CPU-9950X",
        price=Decimal("649.99"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    inv = Inventory(product_id=prod.id, quantity=15, reserved_quantity=0, low_stock_threshold=5)
    db_session.add(inv)
    db_session.commit()

    # Invariant snapshot
    init_qty = inv.quantity
    init_reserved = inv.reserved_quantity

    # 1. Add to cart
    res = client.post("/api/v1/cart/items", json={"product_id": prod.id, "quantity": 3}, headers=headers_c1)
    assert res.status_code == status.HTTP_200_OK

    db_session.refresh(inv)
    assert inv.quantity == init_qty, "Adding to cart MUST NOT modify inventory.quantity!"
    assert inv.reserved_quantity == init_reserved, "Adding to cart MUST NOT reserve inventory!"

    # 2. Update cart quantity
    cart_item_id = res.json()["items"][0]["id"]
    res_update = client.patch(f"/api/v1/cart/items/{cart_item_id}", json={"quantity": 5}, headers=headers_c1)
    assert res_update.status_code == status.HTTP_200_OK

    db_session.refresh(inv)
    assert inv.quantity == init_qty
    assert inv.reserved_quantity == init_reserved

    # 3. Remove from cart
    res_del = client.delete(f"/api/v1/cart/items/{cart_item_id}", headers=headers_c1)
    assert res_del.status_code == status.HTTP_200_OK

    db_session.refresh(inv)
    assert inv.quantity == init_qty
    assert inv.reserved_quantity == init_reserved


# ---------------------------------------------------------------------------
# Phase 6 & 7: Checkout Validation & Atomic Order Creation
# ---------------------------------------------------------------------------

def test_atomic_checkout_order_payment_and_inventory_deduction(db_session, client: TestClient, test_setup):
    headers_c1 = test_setup["headers_cust1"]
    cust1 = test_setup["cust1"]
    cat = test_setup["cat_gpu"]
    brand = test_setup["brand_nvidia"]

    # Setup Product with exactly 10 units
    prod = Product(
        name="GeForce RTX 4070 Ti Super",
        slug="rtx-4070-ti-super",
        sku="GPU-4070TIS",
        price=Decimal("799.99"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    inv = Inventory(product_id=prod.id, quantity=10, reserved_quantity=0, low_stock_threshold=3)
    db_session.add(inv)

    # Customer 1 creates shipping address
    addr = Address(
        user_id=cust1.id,
        recipient_name="Alice Builder",
        phone="09181234567",
        address_line1="456 Silicon Ave",
        barangay="San Antonio",
        city="Pasig",
        province="Metro Manila",
        postal_code="1600",
        country="Philippines",
        is_default=True,
    )
    db_session.add(addr)
    db_session.commit()
    db_session.refresh(addr)

    # Add 2 units to cart
    client.post("/api/v1/cart/items", json={"product_id": prod.id, "quantity": 2}, headers=headers_c1)

    # Validate checkout (Non-destructive)
    res_val = client.post("/api/v1/checkout/validate", json={"address_id": addr.id}, headers=headers_c1)
    assert res_val.status_code == status.HTTP_200_OK
    assert res_val.json()["valid"] is True

    # Execute checkout with Idempotency Key
    idempotency_key = "IDEM-FULL-TEST-001"
    checkout_payload = {
        "address_id": addr.id,
        "payment_method": "CASH_ON_DELIVERY",
        "notes": "Handle with care",
        "idempotency_key": idempotency_key,
    }
    res_checkout = client.post("/api/v1/checkout", json=checkout_payload, headers=headers_c1)
    assert res_checkout.status_code == status.HTTP_201_CREATED
    order_data = res_checkout.json()
    order_id = order_data["id"]

    # 1. Order verification
    assert order_data["total_amount"] == "1599.98"  # 799.99 * 2
    assert order_data["status"] == "CONFIRMED"
    assert order_data["payment_status"] == "PENDING"
    assert order_data["customer_name"] == "Alice Builder"

    # 2. Inventory deduction & audit transaction verification
    db_session.refresh(inv)
    assert inv.quantity == 8, f"Inventory quantity should be 8, got {inv.quantity}"
    tx = (
        db_session.query(InventoryTransaction)
        .filter(InventoryTransaction.product_id == prod.id)
        .order_by(InventoryTransaction.id.desc())
        .first()
    )
    assert tx is not None
    assert tx.type == InventoryTransactionType.SALE.value
    assert tx.quantity_change == -2

    # 3. Payment record verification
    payment = db_session.query(Payment).filter(Payment.order_id == order_id).first()
    assert payment is not None
    assert payment.status == "PENDING"
    assert payment.amount == Decimal("1599.98")
    assert payment.currency == "PHP"

    # 4. Cart cleared verification
    cart_res = client.get("/api/v1/cart", headers=headers_c1)
    assert cart_res.json()["item_count"] == 0

    # 5. Idempotent re-submission returns identical order without double deduction
    res_retry = client.post("/api/v1/checkout", json=checkout_payload, headers=headers_c1)
    assert res_retry.status_code in (status.HTTP_200_OK, status.HTTP_201_CREATED)
    assert res_retry.json()["id"] == order_id
    db_session.refresh(inv)
    assert inv.quantity == 8, "Idempotent checkout MUST NOT double-deduct inventory!"


# ---------------------------------------------------------------------------
# Phase 10: Order Cancellation & Inventory Reversal
# ---------------------------------------------------------------------------

def test_order_cancellation_restores_inventory_and_cancels_payment(db_session, client: TestClient, test_setup):
    headers_c1 = test_setup["headers_cust1"]
    cust1 = test_setup["cust1"]
    cat = test_setup["cat_gpu"]
    brand = test_setup["brand_nvidia"]

    prod = Product(
        name="GeForce RTX 4060",
        slug="rtx-4060",
        sku="GPU-4060",
        price=Decimal("299.99"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    inv = Inventory(product_id=prod.id, quantity=5, reserved_quantity=0, low_stock_threshold=2)
    db_session.add(inv)

    addr = Address(
        user_id=cust1.id,
        recipient_name="Alice Builder",
        phone="09181234567",
        address_line1="456 Silicon Ave",
        barangay="San Antonio",
        city="Pasig",
        province="Metro Manila",
        postal_code="1600",
        country="Philippines",
        is_default=True,
    )
    db_session.add(addr)
    db_session.commit()
    db_session.refresh(addr)

    # Buy 2 units
    client.post("/api/v1/cart/items", json={"product_id": prod.id, "quantity": 2}, headers=headers_c1)
    res_order = client.post("/api/v1/checkout", json={"address_id": addr.id, "payment_method": "CASH_ON_DELIVERY"}, headers=headers_c1)
    order_id = res_order.json()["id"]

    db_session.refresh(inv)
    assert inv.quantity == 3

    # Customer cancels order
    res_cancel = client.post(f"/api/v1/orders/{order_id}/cancel", headers=headers_c1)
    assert res_cancel.status_code == status.HTTP_200_OK
    cancelled_data = res_cancel.json()
    assert cancelled_data["status"] == "CANCELLED"
    assert cancelled_data["payment_status"] == "CANCELLED"

    # Inventory quantity restored to 5
    db_session.refresh(inv)
    assert inv.quantity == 5, f"Expected restored inventory 5, got {inv.quantity}"

    # Verify SALE_REVERSAL audit transaction logged
    reversal_tx = (
        db_session.query(InventoryTransaction)
        .filter(InventoryTransaction.product_id == prod.id)
        .order_by(InventoryTransaction.id.desc())
        .first()
    )
    assert reversal_tx.type == InventoryTransactionType.SALE_REVERSAL.value
    assert reversal_tx.quantity_change == 2

    # Double cancellation is rejected
    res_double = client.post(f"/api/v1/orders/{order_id}/cancel", headers=headers_c1)
    assert res_double.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Phase 11: Payment Admin Collection Workflow
# ---------------------------------------------------------------------------

def test_admin_payment_collection_and_synchronization(db_session, client: TestClient, test_setup):
    headers_c1 = test_setup["headers_cust1"]
    headers_admin = test_setup["headers_admin"]
    cust1 = test_setup["cust1"]
    cat = test_setup["cat_cpu"]
    brand = test_setup["brand_amd"]

    prod = Product(
        name="Ryzen 5 7600",
        slug="ryzen-5-7600",
        sku="CPU-7600",
        price=Decimal("199.99"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    inv = Inventory(product_id=prod.id, quantity=10, reserved_quantity=0, low_stock_threshold=2)
    db_session.add(inv)

    addr = Address(
        user_id=cust1.id,
        recipient_name="Alice Builder",
        phone="09181234567",
        address_line1="456 Silicon Ave",
        barangay="San Antonio",
        city="Pasig",
        province="Metro Manila",
        postal_code="1600",
        country="Philippines",
        is_default=True,
    )
    db_session.add(addr)
    db_session.commit()
    db_session.refresh(addr)

    # Place order
    client.post("/api/v1/cart/items", json={"product_id": prod.id, "quantity": 1}, headers=headers_c1)
    res_order = client.post("/api/v1/checkout", json={"address_id": addr.id, "payment_method": "CASH_ON_DELIVERY"}, headers=headers_c1)
    order_id = res_order.json()["id"]

    # Admin marks payment as PAID
    payment = db_session.query(Payment).filter(Payment.order_id == order_id).first()
    assert payment is not None
    res_pay = client.post(f"/api/v1/admin/payments/{payment.id}/mark-paid", headers=headers_admin)
    assert res_pay.status_code == status.HTTP_200_OK
    pay_data = res_pay.json()
    assert pay_data["status"] == "PAID"
    assert pay_data["paid_at"] is not None

    # Customer order detail reflects PAID status
    res_cust_order = client.get(f"/api/v1/orders/{order_id}", headers=headers_c1)
    assert res_cust_order.status_code == status.HTTP_200_OK
    assert res_cust_order.json()["payment_status"] == "PAID"

    # Paid order cannot be cancelled
    res_cancel = client.post(f"/api/v1/orders/{order_id}/cancel", headers=headers_c1)
    assert res_cancel.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# Phase 12 & 13: Reviews Verified Purchaser & Storefront Aggregations
# ---------------------------------------------------------------------------

def test_reviews_verified_purchaser_rule_and_admin_moderation(db_session, client: TestClient, test_setup):
    headers_c1 = test_setup["headers_cust1"]
    headers_c2 = test_setup["headers_cust2"]
    headers_admin = test_setup["headers_admin"]
    cust1 = test_setup["cust1"]
    cat = test_setup["cat_gpu"]
    brand = test_setup["brand_nvidia"]

    prod = Product(
        name="GeForce RTX 4070 Super",
        slug="rtx-4070-super",
        sku="GPU-4070S",
        price=Decimal("599.99"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    inv = Inventory(product_id=prod.id, quantity=10, reserved_quantity=0, low_stock_threshold=2)
    db_session.add(inv)

    # 1. Cust2 (has never purchased) tries to review -> 403 Forbidden
    res_unverified = client.post(
        f"/api/v1/products/{prod.id}/reviews",
        json={"rating": 5, "title": "Fake review", "comment": "Never bought this"},
        headers=headers_c2,
    )
    assert res_unverified.status_code == status.HTTP_403_FORBIDDEN

    # 2. Cust1 purchases product
    addr = Address(
        user_id=cust1.id,
        recipient_name="Alice Builder",
        phone="09181234567",
        address_line1="456 Silicon Ave",
        barangay="San Antonio",
        city="Pasig",
        province="Metro Manila",
        postal_code="1600",
        country="Philippines",
        is_default=True,
    )
    db_session.add(addr)
    db_session.commit()
    db_session.refresh(addr)

    client.post("/api/v1/cart/items", json={"product_id": prod.id, "quantity": 1}, headers=headers_c1)
    client.post("/api/v1/checkout", json={"address_id": addr.id, "payment_method": "CASH_ON_DELIVERY"}, headers=headers_c1)

    # 3. Cust1 submits verified review -> 201 Created
    res_rev = client.post(
        f"/api/v1/products/{prod.id}/reviews",
        json={"rating": 5, "title": "Great GPU", "comment": "Silent and fast"},
        headers=headers_c1,
    )
    assert res_rev.status_code == status.HTTP_201_CREATED
    rev_id = res_rev.json()["id"]

    # 4. Rating summary verification
    res_sum = client.get(f"/api/v1/products/{prod.id}/reviews/summary")
    assert res_sum.status_code == status.HTTP_200_OK
    assert res_sum.json()["average_rating"] == 5.0
    assert res_sum.json()["total_reviews"] == 1

    # 5. Admin hides review -> storefront aggregate resets to 0
    res_hide = client.patch(f"/api/v1/admin/reviews/{rev_id}/status", json={"status": "HIDDEN"}, headers=headers_admin)
    assert res_hide.status_code == status.HTTP_200_OK

    res_sum_hidden = client.get(f"/api/v1/products/{prod.id}/reviews/summary")
    assert res_sum_hidden.json()["total_reviews"] == 0
    assert res_sum_hidden.json()["average_rating"] == 0.0


# ---------------------------------------------------------------------------
# Phase 14: Admin Dashboard End-to-End Operational Integrity
# ---------------------------------------------------------------------------

def test_admin_dashboard_reflects_actual_domain_data(db_session, client: TestClient, test_setup):
    headers_admin = test_setup["headers_admin"]

    res = client.get("/api/v1/admin/dashboard", headers=headers_admin)
    assert res.status_code == status.HTTP_200_OK
    dash = res.json()

    assert "overview" in dash
    assert "orders_by_status" in dash
    assert "low_stock_products" in dash
    assert "top_selling_products" in dash
    assert "recent_orders" in dash
    assert isinstance(dash["overview"]["total_revenue"], str)
    assert isinstance(dash["orders_by_status"]["total"], int)


# ---------------------------------------------------------------------------
# Phase 19: Concurrency Race Condition Prevention
# ---------------------------------------------------------------------------

def test_insufficient_stock_prevents_overselling(db_session, client: TestClient, test_setup):
    headers_c1 = test_setup["headers_cust1"]
    headers_c2 = test_setup["headers_cust2"]
    cust1 = test_setup["cust1"]
    cust2 = test_setup["cust2"]
    cat = test_setup["cat_cpu"]
    brand = test_setup["brand_amd"]

    # Setup a limited product with exactly 1 unit
    prod = Product(
        name="Ryzen Threadripper Limited",
        slug="threadripper-limited",
        sku="CPU-TR-LTD",
        price=Decimal("2999.99"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)

    inv = Inventory(product_id=prod.id, quantity=1, reserved_quantity=0, low_stock_threshold=1)
    db_session.add(inv)

    addr1 = Address(
        user_id=cust1.id,
        recipient_name="Alice",
        phone="09181234567",
        address_line1="123 Road",
        barangay="San Antonio",
        city="Pasig",
        province="Metro Manila",
        postal_code="1600",
        country="Philippines",
        is_default=True,
    )
    addr2 = Address(
        user_id=cust2.id,
        recipient_name="Bob",
        phone="09187654321",
        address_line1="789 Avenue",
        barangay="San Antonio",
        city="Pasig",
        province="Metro Manila",
        postal_code="1600",
        country="Philippines",
        is_default=True,
    )
    db_session.add_all([addr1, addr2])
    db_session.commit()
    db_session.refresh(addr1)
    db_session.refresh(addr2)

    # Both customers add 1 unit to their carts
    client.post("/api/v1/cart/items", json={"product_id": prod.id, "quantity": 1}, headers=headers_c1)
    client.post("/api/v1/cart/items", json={"product_id": prod.id, "quantity": 1}, headers=headers_c2)

    # Alice checks out first -> succeeds
    res1 = client.post("/api/v1/checkout", json={"address_id": addr1.id, "payment_method": "CASH_ON_DELIVERY"}, headers=headers_c1)
    assert res1.status_code == status.HTTP_201_CREATED

    # Bob attempts checkout next -> blocked with 409 Conflict due to insufficient stock
    res2 = client.post("/api/v1/checkout", json={"address_id": addr2.id, "payment_method": "CASH_ON_DELIVERY"}, headers=headers_c2)
    assert res2.status_code == status.HTTP_409_CONFLICT
    assert "Insufficient stock" in res2.json()["detail"]

    # Verify inventory is exactly 0 and never went negative
    db_session.refresh(inv)
    assert inv.quantity == 0, f"Inventory quantity must be 0, got {inv.quantity}"
