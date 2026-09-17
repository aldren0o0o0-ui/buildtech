from decimal import Decimal
from datetime import datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError
from unittest.mock import patch

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
from app.modules.orders.service import OrderService
from app.modules.payment.models import Payment, PaymentStatus as PaymentDomainStatus
from app.modules.payment.service import PaymentService
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
def second_customer(db_session):
    user = User(
        email="second_customer@example.com",
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
def customer_auth_headers(test_customer_user):
    token = create_access_token(
        subject=test_customer_user.id,
        role=test_customer_user.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_customer_auth_headers(second_customer):
    token = create_access_token(
        subject=second_customer.id,
        role=second_customer.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(test_admin_user):
    token = create_access_token(
        subject=test_admin_user.id,
        role=test_admin_user.role,
    )
    return {"Authorization": f"Bearer {token}"}


def setup_customer_cart(db_session, user_id, product, quantity=2):
    cart = db_session.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db_session.add(cart)
        db_session.commit()
        db_session.refresh(cart)

    db_session.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    item = CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity)
    db_session.add(item)
    db_session.commit()
    return cart


SAMPLE_ADDRESS_PAYLOAD = {
    "customer_name": "Jane Doe",
    "customer_email": "customer@example.com",
    "customer_phone": "+639171234567",
    "shipping_address_line1": "123 Tech Avenue",
    "shipping_barangay": "San Antonio",
    "shipping_city": "Pasig",
    "shipping_province": "Metro Manila",
    "shipping_postal_code": "1605",
    "shipping_country": "Philippines",
    "payment_method": "CASH_ON_DELIVERY",
}


# ===========================================================================
# 1. Model & Database Constraints
# ===========================================================================

def test_payment_model_creation_and_constraints(db_session, test_customer_user, active_product):
    setup_customer_cart(db_session, test_customer_user.id, active_product)

    # Create Order
    order = Order(
        order_number="BT-20260912-TEST01",
        user_id=test_customer_user.id,
        status=OrderStatus.CONFIRMED.value,
        payment_method="CASH_ON_DELIVERY",
        payment_status="PENDING",
        subtotal=Decimal("899.98"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("899.98"),
        customer_name="Jane Doe",
        customer_email="customer@example.com",
        customer_phone="+639171234567",
        shipping_address_line1="123 Tech Avenue",
        shipping_city="Pasig",
        shipping_province="Metro Manila",
        shipping_postal_code="1605",
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)

    # Create Payment
    payment = Payment(
        order_id=order.id,
        payment_reference="PAY-20260912-AAA111",
        method="CASH_ON_DELIVERY",
        status="PENDING",
        amount=order.total_amount,
        currency="PHP",
        provider="COD",
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)

    assert payment.id is not None
    assert payment.order_id == order.id
    assert payment.payment_reference == "PAY-20260912-AAA111"
    assert payment.amount == Decimal("899.98")
    assert payment.currency == "PHP"
    assert payment.provider == "COD"
    assert payment.status == "PENDING"
    assert payment.order is not None
    assert payment.order.order_number == "BT-20260912-TEST01"

    # Enforce 1:1 Unique Constraint on order_id
    duplicate_payment = Payment(
        order_id=order.id,
        payment_reference="PAY-20260912-AAA222",
        method="CASH_ON_DELIVERY",
        status="PENDING",
        amount=order.total_amount,
        currency="PHP",
        provider="COD",
    )
    db_session.add(duplicate_payment)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Enforce Unique Constraint on payment_reference
    second_order = Order(
        order_number="BT-20260912-TEST02",
        user_id=test_customer_user.id,
        status=OrderStatus.CONFIRMED.value,
        payment_method="CASH_ON_DELIVERY",
        payment_status="PENDING",
        subtotal=Decimal("100.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        customer_name="Jane Doe",
        customer_email="customer@example.com",
        customer_phone="+639171234567",
        shipping_address_line1="123 Tech Avenue",
        shipping_city="Pasig",
        shipping_province="Metro Manila",
        shipping_postal_code="1605",
    )
    db_session.add(second_order)
    db_session.commit()
    db_session.refresh(second_order)

    duplicate_ref_payment = Payment(
        order_id=second_order.id,
        payment_reference="PAY-20260912-AAA111",  # Same reference as first payment
        method="CASH_ON_DELIVERY",
        status="PENDING",
        amount=Decimal("100.00"),
        currency="PHP",
        provider="COD",
    )
    db_session.add(duplicate_ref_payment)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ===========================================================================
# 2. COD Order Creation Atomicity & Payment Integration
# ===========================================================================

def test_checkout_creates_pending_cod_payment_atomically(
    client, db_session, test_customer_user, active_product, customer_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=2)

    response = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    assert response.status_code == 201
    data = response.json()

    order_id = data["id"]
    order_number = data["order_number"]
    total_amount = Decimal(str(data["total_amount"]))

    # Verify payment row in database
    payment = db_session.query(Payment).filter(Payment.order_id == order_id).first()
    assert payment is not None
    assert payment.method == "CASH_ON_DELIVERY"
    assert payment.status == "PENDING"
    assert payment.amount == total_amount
    assert payment.currency == "PHP"
    assert payment.provider == "COD"
    assert payment.payment_reference.startswith("PAY-")
    assert payment.paid_at is None
    assert payment.cancelled_at is None

    # Check that payment is also included in order response
    assert "payment" in data
    if data["payment"]:
        assert data["payment"]["payment_reference"] == payment.payment_reference
        assert data["payment"]["status"] == "PENDING"
        assert data["payment"]["method"] == "CASH_ON_DELIVERY"


# ===========================================================================
# 3. Customer Payment Endpoint & Strict Customer Isolation
# ===========================================================================

def test_customer_can_view_own_payment(
    client, db_session, test_customer_user, active_product, customer_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    assert order_res.status_code == 201
    order_data = order_res.json()
    order_id = order_data["id"]

    # Customer queries payment for order
    pay_res = client.get(
        f"/api/v1/orders/{order_id}/payment",
        headers=customer_auth_headers,
    )
    assert pay_res.status_code == 200
    pay_data = pay_res.json()

    assert pay_data["order_id"] == order_id
    assert pay_data["payment_reference"].startswith("PAY-")
    assert pay_data["method"] == "CASH_ON_DELIVERY"
    assert pay_data["status"] == "PENDING"
    assert Decimal(str(pay_data["amount"])) == Decimal("449.99")
    assert pay_data["currency"] == "PHP"


def test_customer_cannot_view_another_customer_payment(
    client,
    db_session,
    test_customer_user,
    second_customer,
    active_product,
    customer_auth_headers,
    second_customer_auth_headers,
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    # Customer 1 places order
    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["id"]

    # Customer 2 attempts to query Customer 1's payment
    cross_res = client.get(
        f"/api/v1/orders/{order_id}/payment",
        headers=second_customer_auth_headers,
    )
    # Must return 404 to avoid leaking existence of another customer's order/payment
    assert cross_res.status_code == 404
    assert "not found" in cross_res.json()["detail"].lower()


def test_unauthenticated_payment_access_rejected(client, db_session, test_customer_user, active_product, customer_auth_headers):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["id"]

    # Query without auth token
    unauth_res = client.get(f"/api/v1/orders/{order_id}/payment")
    assert unauth_res.status_code == 401


# ===========================================================================
# 4. State Machine Validation
# ===========================================================================

def test_payment_state_machine_valid_transitions(
    client, db_session, test_customer_user, active_product, customer_auth_headers, admin_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["id"]

    payment = db_session.query(Payment).filter(Payment.order_id == order_id).first()
    payment_id = payment.id

    # 1. PENDING -> FAILED
    res = client.patch(
        f"/api/v1/admin/payments/{payment_id}/status",
        json={"status": "FAILED"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "FAILED"
    assert res.json()["failed_at"] is not None

    # 2. FAILED -> PENDING
    res = client.patch(
        f"/api/v1/admin/payments/{payment_id}/status",
        json={"status": "PENDING"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "PENDING"

    # 3. PENDING -> PAID
    res = client.patch(
        f"/api/v1/admin/payments/{payment_id}/status",
        json={"status": "PAID"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "PAID"
    assert res.json()["paid_at"] is not None

    # 4. PAID -> REFUNDED
    res = client.patch(
        f"/api/v1/admin/payments/{payment_id}/status",
        json={"status": "REFUNDED"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "REFUNDED"


def test_payment_state_machine_invalid_transitions_rejected(
    client, db_session, test_customer_user, active_product, customer_auth_headers, admin_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    order_id = order_res.json()["id"]
    payment = db_session.query(Payment).filter(Payment.order_id == order_id).first()
    payment_id = payment.id

    # Mark as PAID
    client.patch(
        f"/api/v1/admin/payments/{payment_id}/status",
        json={"status": "PAID"},
        headers=admin_auth_headers,
    )

    # Invalid: PAID -> PENDING
    res = client.patch(
        f"/api/v1/admin/payments/{payment_id}/status",
        json={"status": "PENDING"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 400
    assert "invalid payment status transition" in res.json()["detail"].lower()

    # Invalid: PAID -> FAILED
    res = client.patch(
        f"/api/v1/admin/payments/{payment_id}/status",
        json={"status": "FAILED"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 400

    # Invalid: PAID -> CANCELLED
    res = client.patch(
        f"/api/v1/admin/payments/{payment_id}/status",
        json={"status": "CANCELLED"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 400

    # Transition PAID -> REFUNDED (valid)
    client.patch(
        f"/api/v1/admin/payments/{payment_id}/status",
        json={"status": "REFUNDED"},
        headers=admin_auth_headers,
    )

    # Invalid: REFUNDED -> PAID
    res = client.patch(
        f"/api/v1/admin/payments/{payment_id}/status",
        json={"status": "PAID"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 400

    # Invalid: REFUNDED -> PENDING
    res = client.patch(
        f"/api/v1/admin/payments/{payment_id}/status",
        json={"status": "PENDING"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 400


# ===========================================================================
# 5. Admin Mark COD Payment as Paid
# ===========================================================================

def test_admin_mark_cod_paid_success(
    client, db_session, test_customer_user, active_product, customer_auth_headers, admin_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    order_id = order_res.json()["id"]
    payment = db_session.query(Payment).filter(Payment.order_id == order_id).first()
    payment_id = payment.id

    # Admin marks COD as PAID
    mark_res = client.post(
        f"/api/v1/admin/payments/{payment_id}/mark-paid",
        headers=admin_auth_headers,
    )
    assert mark_res.status_code == 200
    data = mark_res.json()
    assert data["status"] == "PAID"
    assert data["paid_at"] is not None

    # Check synchronized database state
    db_session.refresh(payment)
    assert payment.status == "PAID"
    assert payment.paid_at is not None

    # Check order payment status was synchronized
    order = db_session.query(Order).filter(Order.id == order_id).first()
    assert order.payment_status == "PAID"


def test_customer_cannot_mark_payment_as_paid(
    client, db_session, test_customer_user, active_product, customer_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    order_id = order_res.json()["id"]
    payment = db_session.query(Payment).filter(Payment.order_id == order_id).first()

    # Customer tries to mark paid
    res = client.post(
        f"/api/v1/admin/payments/{payment.id}/mark-paid",
        headers=customer_auth_headers,
    )
    assert res.status_code == 403


def test_admin_mark_cod_paid_rejected_if_already_paid(
    client, db_session, test_customer_user, active_product, customer_auth_headers, admin_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    order_id = order_res.json()["id"]
    payment = db_session.query(Payment).filter(Payment.order_id == order_id).first()

    # First call: succeeds
    res1 = client.post(
        f"/api/v1/admin/payments/{payment.id}/mark-paid",
        headers=admin_auth_headers,
    )
    assert res1.status_code == 200

    # Second call: fails (already paid)
    res2 = client.post(
        f"/api/v1/admin/payments/{payment.id}/mark-paid",
        headers=admin_auth_headers,
    )
    assert res2.status_code == 400
    assert "already in status 'paid'" in res2.json()["detail"].lower()


# ===========================================================================
# 6. Admin Payment Listing, Search, and Filtering
# ===========================================================================

def test_admin_list_and_filter_payments(
    client, db_session, test_customer_user, active_product, customer_auth_headers, admin_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    assert order_res.status_code == 201

    # Admin lists all payments
    res = client.get("/api/v1/admin/payments", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1

    first_item = data["items"][0]
    assert "payment_reference" in first_item
    assert "method" in first_item
    assert "status" in first_item
    assert "amount" in first_item
    assert "currency" in first_item
    assert "provider" in first_item

    # Test status filter
    filter_res = client.get(
        "/api/v1/admin/payments?status=PENDING",
        headers=admin_auth_headers,
    )
    assert filter_res.status_code == 200
    assert all(item["status"] == "PENDING" for item in filter_res.json()["items"])

    # Test search by reference
    ref = first_item["payment_reference"]
    search_res = client.get(
        f"/api/v1/admin/payments?search={ref}",
        headers=admin_auth_headers,
    )
    assert search_res.status_code == 200
    assert any(item["payment_reference"] == ref for item in search_res.json()["items"])


# ===========================================================================
# 7. Order Cancellation Integration with Payment
# ===========================================================================

def test_order_cancellation_cancels_pending_payment(
    client, db_session, test_customer_user, active_product, customer_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    order_id = order_res.json()["id"]

    # Customer cancels the order
    cancel_res = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers=customer_auth_headers,
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"

    # Verify payment status was transitioned to CANCELLED
    payment = db_session.query(Payment).filter(Payment.order_id == order_id).first()
    assert payment.status == "CANCELLED"
    assert payment.cancelled_at is not None


def test_order_cancellation_rejected_if_payment_is_paid(
    client, db_session, test_customer_user, active_product, customer_auth_headers, admin_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    order_id = order_res.json()["id"]
    payment = db_session.query(Payment).filter(Payment.order_id == order_id).first()

    # Admin marks COD as PAID
    mark_res = client.post(
        f"/api/v1/admin/payments/{payment.id}/mark-paid",
        headers=admin_auth_headers,
    )
    assert mark_res.status_code == 200

    # Customer attempts to cancel paid order -> must be rejected
    cancel_res = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers=customer_auth_headers,
    )
    assert cancel_res.status_code == 400
    assert "already been paid" in cancel_res.json()["detail"].lower()


# ===========================================================================
# 8. Transactional Atomicity & Rollback
# ===========================================================================

def test_checkout_atomicity_on_payment_creation_failure(
    client, db_session, test_customer_user, active_product, customer_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=2)
    inv_before = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first().quantity

    # Simulate payment creation failure inside the transaction
    with patch.object(
        PaymentService,
        "create_payment_for_order",
        side_effect=RuntimeError("Payment gateway initialization fault"),
    ):
        res = client.post(
            "/api/v1/orders",
            json=SAMPLE_ADDRESS_PAYLOAD,
            headers=customer_auth_headers,
        )
        assert res.status_code == 500

    # Invariant: Nothing should have been committed
    orders_count = db_session.query(Order).count()
    payments_count = db_session.query(Payment).count()
    order_items_count = db_session.query(OrderItem).count()
    sale_tx_count = (
        db_session.query(InventoryTransaction)
        .filter(InventoryTransaction.type == InventoryTransactionType.SALE.value)
        .count()
    )
    inv_after = db_session.query(Inventory).filter(Inventory.product_id == active_product.id).first().quantity

    assert orders_count == 0
    assert payments_count == 0
    assert order_items_count == 0
    assert sale_tx_count == 0
    assert inv_after == inv_before  # Stock was NOT decremented

    # Customer cart is still intact
    cart = db_session.query(Cart).filter(Cart.user_id == test_customer_user.id).first()
    assert len(cart.items) == 1


# ===========================================================================
# 9. Idempotency Preserves Payment
# ===========================================================================

def test_checkout_idempotency_preserves_payment(
    client, db_session, test_customer_user, active_product, customer_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    headers = {**customer_auth_headers, "Idempotency-Key": "IDEM-PAY-TEST-999"}

    # First request
    res1 = client.post("/api/v1/orders", json=SAMPLE_ADDRESS_PAYLOAD, headers=headers)
    assert res1.status_code == 201
    order1 = res1.json()

    # Duplicate request with same Idempotency-Key
    res2 = client.post("/api/v1/orders", json=SAMPLE_ADDRESS_PAYLOAD, headers=headers)
    assert res2.status_code in (200, 201)
    order2 = res2.json()

    # Must return identical order
    assert order1["id"] == order2["id"]
    assert order1["order_number"] == order2["order_number"]

    # Verify only 1 Payment record was created in DB
    payments = db_session.query(Payment).filter(Payment.order_id == order1["id"]).all()
    assert len(payments) == 1


# ===========================================================================
# 10. Additional Edge Cases & Error Handling
# ===========================================================================

def test_admin_get_payment_detail_by_id(
    client, db_session, test_customer_user, active_product, customer_auth_headers, admin_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    order_id = order_res.json()["id"]
    payment = db_session.query(Payment).filter(Payment.order_id == order_id).first()

    res = client.get(
        f"/api/v1/admin/payments/{payment.id}",
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == payment.id
    assert data["payment_reference"] == payment.payment_reference
    assert data["provider"] == "COD"
    assert data["customer_name"] == "Jane Doe"
    assert data["customer_email"] == "customer@example.com"
    assert data["order_number"] == order_res.json()["order_number"]


def test_admin_get_payment_nonexistent_returns_404(client, admin_auth_headers):
    res = client.get("/api/v1/admin/payments/999999", headers=admin_auth_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_admin_mark_cod_paid_nonexistent_returns_404(client, admin_auth_headers):
    res = client.post("/api/v1/admin/payments/999999/mark-paid", headers=admin_auth_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_admin_update_status_nonexistent_returns_404(client, admin_auth_headers):
    res = client.patch(
        "/api/v1/admin/payments/999999/status",
        json={"status": "PAID"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_admin_update_status_unauthorized_fails(
    client, db_session, test_customer_user, active_product, customer_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    order_id = order_res.json()["id"]
    payment = db_session.query(Payment).filter(Payment.order_id == order_id).first()

    res = client.patch(
        f"/api/v1/admin/payments/{payment.id}/status",
        json={"status": "PAID"},
        headers=customer_auth_headers,
    )
    assert res.status_code == 403


def test_admin_update_same_status_is_noop(
    client, db_session, test_customer_user, active_product, customer_auth_headers, admin_auth_headers
):
    setup_customer_cart(db_session, test_customer_user.id, active_product, quantity=1)

    order_res = client.post(
        "/api/v1/orders",
        json=SAMPLE_ADDRESS_PAYLOAD,
        headers=customer_auth_headers,
    )
    order_id = order_res.json()["id"]
    payment = db_session.query(Payment).filter(Payment.order_id == order_id).first()

    # Update to current status (PENDING) -> returns payment as-is
    res = client.patch(
        f"/api/v1/admin/payments/{payment.id}/status",
        json={"status": "PENDING"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "PENDING"

