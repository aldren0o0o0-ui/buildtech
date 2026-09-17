from decimal import Decimal
from datetime import datetime, timezone
import pytest
from app.core.status import status
from app.core.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.modules.addresses.models import Address
from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.dashboard.service import DashboardService
from app.modules.inventory.models import Inventory
from app.modules.orders.models import Order, OrderItem, OrderStatus, PaymentStatus
from app.modules.products.models import Product, ProductStatus
from app.modules.users.models import User, UserRole


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user(db_session):
    admin = User(
        email="dashboard_admin@buildtech.com",
        password_hash=hash_password("AdminPass123!"),
        first_name="Admin",
        last_name="Commander",
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def admin_headers(admin_user):
    token = create_access_token(subject=admin_user.id, role=admin_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def customer_user(db_session):
    customer = User(
        email="dashboard_customer@buildtech.com",
        password_hash=hash_password("CustomerPass123!"),
        first_name="John",
        last_name="Buyer",
        role=UserRole.CUSTOMER.value,
        is_active=True,
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def customer_headers(customer_user):
    token = create_access_token(subject=customer_user.id, role=customer_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def catalog_setup(db_session):
    category = Category(name="Processors", slug="processors", is_active=True)
    brand = Brand(name="AMD", slug="amd", is_active=True)
    db_session.add_all([category, brand])
    db_session.commit()
    db_session.refresh(category)
    db_session.refresh(brand)
    return category, brand


# ---------------------------------------------------------------------------
# Security Tests
# ---------------------------------------------------------------------------

def test_guest_cannot_access_dashboard(client: TestClient):
    response = client.get("/api/v1/admin/dashboard")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_customer_cannot_access_dashboard(client: TestClient, customer_headers):
    response = client.get("/api/v1/admin/dashboard", headers=customer_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_access_empty_dashboard(client: TestClient, admin_headers):
    response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert "overview" in data
    assert "orders_by_status" in data
    assert "low_stock_products" in data
    assert "top_selling_products" in data
    assert "recent_orders" in data

    overview = data["overview"]
    assert overview["total_revenue"] == "0.00"
    assert overview["pending_payment"] == "0.00"
    assert overview["total_order_value"] == "0.00"
    assert overview["total_orders"] == 0
    assert overview["total_customers"] == 0
    assert overview["total_products"] == 0

    assert data["orders_by_status"]["total"] == 0
    assert data["low_stock_products"] == []
    assert data["top_selling_products"] == []
    assert data["recent_orders"] == []


# ---------------------------------------------------------------------------
# Metric & Data Tests
# ---------------------------------------------------------------------------

def test_revenue_and_pending_payment_calculation(db_session, client: TestClient, admin_headers, customer_user, catalog_setup):
    """
    Test revenue semantics:
    - Order 1: 1,500.00, PAID -> counts towards total_revenue and total_order_value
    - Order 2: 2,500.00, PENDING -> counts towards pending_payment and total_order_value
    - Order 3: 4,000.00, CANCELLED -> strictly EXCLUDED from total_revenue and pending_payment
    """
    cat, brand = catalog_setup

    o1 = Order(
        order_number="ORD-TEST-001",
        user_id=customer_user.id,
        status=OrderStatus.DELIVERED.value,
        payment_status=PaymentStatus.PAID.value,
        subtotal=Decimal("1500.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("1500.00"),
        customer_name="John Buyer",
        customer_email=customer_user.email,
        customer_phone="09171234567",
        shipping_address_line1="123 Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
    )
    o2 = Order(
        order_number="ORD-TEST-002",
        user_id=customer_user.id,
        status=OrderStatus.CONFIRMED.value,
        payment_status=PaymentStatus.PENDING.value,
        subtotal=Decimal("2500.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("2500.00"),
        customer_name="John Buyer",
        customer_email=customer_user.email,
        customer_phone="09171234567",
        shipping_address_line1="123 Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
    )
    o3 = Order(
        order_number="ORD-TEST-003",
        user_id=customer_user.id,
        status=OrderStatus.CANCELLED.value,
        payment_status=PaymentStatus.CANCELLED.value,
        subtotal=Decimal("4000.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("4000.00"),
        customer_name="John Buyer",
        customer_email=customer_user.email,
        customer_phone="09171234567",
        shipping_address_line1="123 Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
    )
    db_session.add_all([o1, o2, o3])
    db_session.commit()

    response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    overview = response.json()["overview"]

    assert overview["total_revenue"] == "1500.00"
    assert overview["pending_payment"] == "2500.00"
    assert overview["total_order_value"] == "4000.00"
    assert overview["total_orders"] == 3


def test_order_status_counts_aggregation(db_session, client: TestClient, admin_headers, customer_user):
    orders = [
        Order(
            order_number=f"ORD-STATUS-{i}",
            user_id=customer_user.id,
            status=st,
            payment_status=PaymentStatus.PENDING.value,
            subtotal=Decimal("100.00"),
            shipping_fee=Decimal("0.00"),
            total_amount=Decimal("100.00"),
            customer_name="John Buyer",
            customer_email=customer_user.email,
            customer_phone="09171234567",
            shipping_address_line1="Street",
            shipping_city="City",
            shipping_province="Province",
            shipping_postal_code="1000",
        )
        for i, st in enumerate([
            OrderStatus.PENDING.value,
            OrderStatus.CONFIRMED.value,
            OrderStatus.CONFIRMED.value,
            OrderStatus.PROCESSING.value,
            OrderStatus.SHIPPED.value,
            OrderStatus.DELIVERED.value,
            OrderStatus.CANCELLED.value,
        ])
    ]
    db_session.add_all(orders)
    db_session.commit()

    response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    status_counts = response.json()["orders_by_status"]

    assert status_counts["pending"] == 1
    assert status_counts["confirmed"] == 2
    assert status_counts["processing"] == 1
    assert status_counts["shipped"] == 1
    assert status_counts["delivered"] == 1
    assert status_counts["cancelled"] == 1
    assert status_counts["total"] == 7


def test_customer_metrics_excludes_administrators(db_session, client: TestClient, admin_headers, customer_user):
    # Add a second inactive customer
    inactive_customer = User(
        email="inactive@example.com",
        password_hash=hash_password("Pass123!"),
        first_name="Inactive",
        last_name="User",
        role=UserRole.CUSTOMER.value,
        is_active=False,
    )
    # Add another admin (should not be counted in customer metrics)
    another_admin = User(
        email="admin2@example.com",
        password_hash=hash_password("Pass123!"),
        first_name="Admin",
        last_name="Two",
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db_session.add_all([inactive_customer, another_admin])
    db_session.commit()

    response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    overview = response.json()["overview"]

    # Exactly 2 customers (1 active, 1 inactive), admins excluded
    assert overview["total_customers"] == 2
    assert overview["active_customers"] == 1


def test_product_metrics_tracks_active_and_total(db_session, client: TestClient, admin_headers, catalog_setup):
    cat, brand = catalog_setup

    p1 = Product(
        name="Ryzen 7 7800X3D",
        slug="ryzen-7-7800x3d",
        sku="CPU-7800X3D",
        price=Decimal("449.99"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    p2 = Product(
        name="Ryzen 5 7600X",
        slug="ryzen-5-7600x",
        sku="CPU-7600X",
        price=Decimal("229.99"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    p3 = Product(
        name="Ryzen 9 7950X Retired",
        slug="ryzen-9-7950x-old",
        sku="CPU-7950X-OLD",
        price=Decimal("599.99"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ARCHIVED.value,
    )
    db_session.add_all([p1, p2, p3])
    db_session.commit()

    response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    overview = response.json()["overview"]

    assert overview["total_products"] == 3
    assert overview["active_products"] == 2


def test_low_stock_detection_respects_reserved_quantity(db_session, client: TestClient, admin_headers, catalog_setup):
    cat, brand = catalog_setup

    # Product A: quantity=10, reserved=7 -> available=3 (<= threshold 5) -> LOW_STOCK
    p_low = Product(
        name="GeForce RTX 4070",
        slug="rtx-4070",
        sku="GPU-4070",
        price=Decimal("599.99"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    # Product B: quantity=20, reserved=2 -> available=18 (> threshold 5) -> HEALTHY (not in list)
    p_healthy = Product(
        name="GeForce RTX 4090",
        slug="rtx-4090",
        sku="GPU-4090",
        price=Decimal("1599.99"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    # Product C: quantity=0, reserved=0 -> available=0 (<= threshold 5) -> OUT_OF_STOCK
    p_out = Product(
        name="Radeon RX 7900 XTX",
        slug="rx-7900-xtx",
        sku="GPU-7900XTX",
        price=Decimal("999.99"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    db_session.add_all([p_low, p_healthy, p_out])
    db_session.commit()

    inv_low = Inventory(product_id=p_low.id, quantity=10, reserved_quantity=7, low_stock_threshold=5)
    inv_healthy = Inventory(product_id=p_healthy.id, quantity=20, reserved_quantity=2, low_stock_threshold=5)
    inv_out = Inventory(product_id=p_out.id, quantity=0, reserved_quantity=0, low_stock_threshold=5)
    db_session.add_all([inv_low, inv_healthy, inv_out])
    db_session.commit()

    response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    low_stock = response.json()["low_stock_products"]

    low_stock_ids = [item["product_id"] for item in low_stock]
    assert p_out.id in low_stock_ids
    assert p_low.id in low_stock_ids
    assert p_healthy.id not in low_stock_ids

    # Out of stock item should be first (available=0)
    out_item = next(i for i in low_stock if i["product_id"] == p_out.id)
    assert out_item["available_quantity"] == 0
    assert out_item["availability_status"] == "OUT_OF_STOCK"

    low_item = next(i for i in low_stock if i["product_id"] == p_low.id)
    assert low_item["available_quantity"] == 3
    assert low_item["availability_status"] == "LOW_STOCK"


def test_top_selling_products_aggregation_excludes_cancelled(db_session, client: TestClient, admin_headers, customer_user, catalog_setup):
    cat, brand = catalog_setup

    prod_a = Product(
        name="Core i7 14700K",
        slug="core-i7-14700k",
        sku="CPU-14700K",
        price=Decimal("400.00"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    prod_b = Product(
        name="Core i5 14600K",
        slug="core-i5-14600k",
        sku="CPU-14600K",
        price=Decimal("300.00"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    prod_c = Product(
        name="Core i9 14900KS",
        slug="core-i9-14900ks",
        sku="CPU-14900KS",
        price=Decimal("700.00"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    db_session.add_all([prod_a, prod_b, prod_c])
    db_session.commit()

    # Confirmed order 1: Prod A (qty 3), Prod B (qty 1)
    o1 = Order(
        order_number="ORD-SALE-001",
        user_id=customer_user.id,
        status=OrderStatus.CONFIRMED.value,
        payment_status=PaymentStatus.PAID.value,
        subtotal=Decimal("1500.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("1500.00"),
        customer_name="John Buyer",
        customer_email=customer_user.email,
        customer_phone="09171234567",
        shipping_address_line1="Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
    )
    db_session.add(o1)
    db_session.commit()

    item_a1 = OrderItem(
        order_id=o1.id,
        product_id=prod_a.id,
        product_name=prod_a.name,
        product_sku=prod_a.sku,
        product_slug=prod_a.slug,
        quantity=3,
        unit_price=Decimal("400.00"),
        subtotal=Decimal("1200.00"),
    )
    item_b1 = OrderItem(
        order_id=o1.id,
        product_id=prod_b.id,
        product_name=prod_b.name,
        product_sku=prod_b.sku,
        product_slug=prod_b.slug,
        quantity=1,
        unit_price=Decimal("300.00"),
        subtotal=Decimal("300.00"),
    )
    db_session.add_all([item_a1, item_b1])

    # Delivered order 2: Prod A (qty 2)
    o2 = Order(
        order_number="ORD-SALE-002",
        user_id=customer_user.id,
        status=OrderStatus.DELIVERED.value,
        payment_status=PaymentStatus.PAID.value,
        subtotal=Decimal("800.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("800.00"),
        customer_name="John Buyer",
        customer_email=customer_user.email,
        customer_phone="09171234567",
        shipping_address_line1="Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
    )
    db_session.add(o2)
    db_session.commit()

    item_a2 = OrderItem(
        order_id=o2.id,
        product_id=prod_a.id,
        product_name=prod_a.name,
        product_sku=prod_a.sku,
        product_slug=prod_a.slug,
        quantity=2,
        unit_price=Decimal("400.00"),
        subtotal=Decimal("800.00"),
    )
    db_session.add(item_a2)

    # Cancelled order 3: Prod C (qty 50) -> MUST NOT BE COUNTED
    o3 = Order(
        order_number="ORD-SALE-003",
        user_id=customer_user.id,
        status=OrderStatus.CANCELLED.value,
        payment_status=PaymentStatus.CANCELLED.value,
        subtotal=Decimal("35000.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("35000.00"),
        customer_name="John Buyer",
        customer_email=customer_user.email,
        customer_phone="09171234567",
        shipping_address_line1="Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
    )
    db_session.add(o3)
    db_session.commit()

    item_c = OrderItem(
        order_id=o3.id,
        product_id=prod_c.id,
        product_name=prod_c.name,
        product_sku=prod_c.sku,
        product_slug=prod_c.slug,
        quantity=50,
        unit_price=Decimal("700.00"),
        subtotal=Decimal("35000.00"),
    )
    db_session.add(item_c)
    db_session.commit()

    response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    top_products = response.json()["top_selling_products"]

    # Prod C from cancelled order MUST NOT be present
    assert not any(p["product_id"] == prod_c.id for p in top_products)

    # Prod A should be #1 with 5 units (3 + 2) and 2000.00 total sales
    assert len(top_products) >= 2
    assert top_products[0]["product_id"] == prod_a.id
    assert top_products[0]["units_sold"] == 5
    assert top_products[0]["total_sales"] == "2000.00"

    # Prod B should be #2 with 1 unit and 300.00 total sales
    assert top_products[1]["product_id"] == prod_b.id
    assert top_products[1]["units_sold"] == 1
    assert top_products[1]["total_sales"] == "300.00"


def test_recent_orders_ordering_and_fields(db_session, client: TestClient, admin_headers, customer_user):
    o1 = Order(
        order_number="ORD-REC-001",
        user_id=customer_user.id,
        status=OrderStatus.PENDING.value,
        payment_status=PaymentStatus.PENDING.value,
        subtotal=Decimal("100.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("100.00"),
        customer_name="John Buyer",
        customer_email=customer_user.email,
        customer_phone="09171234567",
        shipping_address_line1="Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
    )
    o2 = Order(
        order_number="ORD-REC-002",
        user_id=customer_user.id,
        status=OrderStatus.CONFIRMED.value,
        payment_status=PaymentStatus.PAID.value,
        subtotal=Decimal("200.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("200.00"),
        customer_name="John Buyer",
        customer_email=customer_user.email,
        customer_phone="09171234567",
        shipping_address_line1="Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
    )
    db_session.add_all([o1, o2])
    db_session.commit()

    response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    recent_orders = response.json()["recent_orders"]

    assert len(recent_orders) >= 2
    # Order 2 was created after Order 1, so it should be first
    assert recent_orders[0]["order_number"] == "ORD-REC-002"
    assert recent_orders[0]["total_amount"] == "200.00"
    assert recent_orders[0]["payment_status"] == "PAID"
    assert recent_orders[0]["status"] == "CONFIRMED"
    assert recent_orders[0]["customer_name"] == "John Buyer"


def test_dashboard_service_direct_execution(db_session):
    result = DashboardService.get_dashboard_data(db_session)
    assert result.overview.total_revenue == "0.00"
    assert result.orders_by_status.total == 0
    assert isinstance(result.low_stock_products, list)
    assert isinstance(result.top_selling_products, list)
    assert isinstance(result.recent_orders, list)


def test_recent_orders_limit_capped_at_ten(db_session, client: TestClient, admin_headers, customer_user):
    orders = [
        Order(
            order_number=f"ORD-LIM-{i:02d}",
            user_id=customer_user.id,
            status=OrderStatus.CONFIRMED.value,
            payment_status=PaymentStatus.PAID.value,
            subtotal=Decimal("10.00"),
            shipping_fee=Decimal("0.00"),
            total_amount=Decimal("10.00"),
            customer_name="John Buyer",
            customer_email=customer_user.email,
            customer_phone="09171234567",
            shipping_address_line1="Street",
            shipping_city="City",
            shipping_province="Province",
            shipping_postal_code="1000",
        )
        for i in range(15)
    ]
    db_session.add_all(orders)
    db_session.commit()

    response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    recent_orders = response.json()["recent_orders"]
    assert len(recent_orders) == 10
    # The first one should be the last inserted
    assert recent_orders[0]["order_number"] == "ORD-LIM-14"


def test_low_stock_threshold_custom_values(db_session, client: TestClient, admin_headers, catalog_setup):
    cat, brand = catalog_setup
    p_high_threshold = Product(
        name="Custom High Threshold",
        slug="custom-high-threshold",
        sku="SKU-HIGH",
        price=Decimal("100.00"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    p_low_threshold = Product(
        name="Custom Low Threshold",
        slug="custom-low-threshold",
        sku="SKU-LOW",
        price=Decimal("100.00"),
        category_id=cat.id,
        brand_id=brand.id,
        status=ProductStatus.ACTIVE.value,
    )
    db_session.add_all([p_high_threshold, p_low_threshold])
    db_session.commit()

    # Product with quantity 8 and threshold 10 -> Low stock (8 <= 10)
    inv1 = Inventory(product_id=p_high_threshold.id, quantity=8, reserved_quantity=0, low_stock_threshold=10)
    # Product with quantity 8 and threshold 2 -> Healthy (8 > 2)
    inv2 = Inventory(product_id=p_low_threshold.id, quantity=8, reserved_quantity=0, low_stock_threshold=2)
    db_session.add_all([inv1, inv2])
    db_session.commit()

    response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    low_stock_ids = [item["product_id"] for item in response.json()["low_stock_products"]]

    assert p_high_threshold.id in low_stock_ids
    assert p_low_threshold.id not in low_stock_ids


def test_top_selling_empty_when_no_sales(db_session, client: TestClient, admin_headers):
    response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["top_selling_products"] == []


def test_multiple_orders_different_statuses_revenue_isolation(db_session, client: TestClient, admin_headers, customer_user):
    # Completed order with paid status
    o_comp = Order(
        order_number="ORD-REV-COMP",
        user_id=customer_user.id,
        status=OrderStatus.COMPLETED.value,
        payment_status=PaymentStatus.PAID.value,
        subtotal=Decimal("5000.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("5000.00"),
        customer_name="John Buyer",
        customer_email=customer_user.email,
        customer_phone="09171234567",
        shipping_address_line1="Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
    )
    # Cancelled order with paid status (e.g. refunded or cancelled before processing)
    # Total order value should EXCLUDE cancelled orders
    o_canc = Order(
        order_number="ORD-REV-CANC",
        user_id=customer_user.id,
        status=OrderStatus.CANCELLED.value,
        payment_status=PaymentStatus.CANCELLED.value,
        subtotal=Decimal("2000.00"),
        shipping_fee=Decimal("0.00"),
        total_amount=Decimal("2000.00"),
        customer_name="John Buyer",
        customer_email=customer_user.email,
        customer_phone="09171234567",
        shipping_address_line1="Street",
        shipping_city="City",
        shipping_province="Province",
        shipping_postal_code="1000",
    )
    db_session.add_all([o_comp, o_canc])
    db_session.commit()

    response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    overview = response.json()["overview"]

    assert overview["total_revenue"] == "5000.00"
    assert overview["total_order_value"] == "5000.00"
    assert overview["total_orders"] == 2

