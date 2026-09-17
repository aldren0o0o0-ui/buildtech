"""
API Integration Tests for Compatibility Engine Endpoint (Module 14).
"""

from decimal import Decimal
import pytest

from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.inventory.models import Inventory
from app.modules.orders.models import Order
from app.modules.carts.models import CartItem
from app.modules.payment.models import Payment
from app.modules.products.models import Product, ProductStatus
from app.modules.products.specifications.models import (
    CpuSpecification,
    MotherboardSpecification,
)


@pytest.fixture
def sample_hardware(db_session):
    cat_cpu = Category(name="Processors", slug="cpu", is_active=True)
    cat_mb = Category(name="Motherboards", slug="motherboard", is_active=True)
    brand = Brand(name="Test Brand", slug="test-brand", is_active=True)
    db_session.add_all([cat_cpu, cat_mb, brand])
    db_session.commit()

    cpu = Product(
        sku="CPU-AM5-TEST",
        name="AMD Ryzen 5 7600",
        slug="amd-ryzen-5-7600",
        category_id=cat_cpu.id,
        brand_id=brand.id,
        price=Decimal("199.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    mb = Product(
        sku="MB-AM5-TEST",
        name="MSI Pro B650M-A",
        slug="msi-pro-b650m-a",
        category_id=cat_mb.id,
        brand_id=brand.id,
        price=Decimal("139.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add_all([cpu, mb])
    db_session.commit()

    cpu_spec = CpuSpecification(
        product_id=cpu.id,
        socket="AM5",
        core_count=6,
        thread_count=12,
        base_clock_ghz=Decimal("3.80"),
        boost_clock_ghz=Decimal("5.10"),
        tdp_watts=65,
    )
    mb_spec = MotherboardSpecification(
        product_id=mb.id,
        socket="AM5",
        chipset="B650",
        form_factor="Micro-ATX",
        memory_type="DDR5",
        memory_slots=4,
        max_memory_gb=128,
        wifi=False,
    )
    # Inventory records
    inv_cpu = Inventory(product_id=cpu.id, quantity=10, reserved_quantity=0)
    inv_mb = Inventory(product_id=mb.id, quantity=15, reserved_quantity=0)

    db_session.add_all([cpu_spec, mb_spec, inv_cpu, inv_mb])
    db_session.commit()

    return {"cpu": cpu, "mb": mb, "inv_cpu": inv_cpu, "inv_mb": inv_mb}


def test_api_compatibility_check_success(client, sample_hardware):
    cpu = sample_hardware["cpu"]
    mb = sample_hardware["mb"]

    payload = {"product_ids": [cpu.id, mb.id]}
    response = client.post("/api/v1/compatibility/check", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "summary" in data
    assert "checks" in data
    assert data["component_count"] == 2
    assert any(check["rule"] == "CPU_SOCKET" and check["status"] == "PASS" for check in data["checks"])


def test_api_compatibility_check_invalid_product_id(client, sample_hardware):
    payload = {"product_ids": [99999]}
    response = client.post("/api/v1/compatibility/check", json=payload)

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_api_compatibility_check_empty_payload(client):
    payload = {"product_ids": []}
    response = client.post("/api/v1/compatibility/check", json=payload)

    assert response.status_code == 422


def test_api_compatibility_check_extra_field_forbidden(client, sample_hardware):
    payload = {
        "product_ids": [sample_hardware["cpu"].id],
        "injected_spec": {"socket": "AM5"},  # Should be forbidden
    }
    response = client.post("/api/v1/compatibility/check", json=payload)

    assert response.status_code == 422


def test_api_compatibility_public_access(client, sample_hardware):
    """Verify endpoint is accessible publicly without any authentication headers."""
    payload = {"product_ids": [sample_hardware["cpu"].id, sample_hardware["mb"].id]}
    response = client.post("/api/v1/compatibility/check", json=payload)

    assert response.status_code == 200


def test_api_compatibility_read_only_no_mutations(client, db_session, sample_hardware):
    """Verify that checking compatibility produces zero mutations across database tables."""
    cpu = sample_hardware["cpu"]
    mb = sample_hardware["mb"]

    # Initial states
    initial_inv_cpu_qty = sample_hardware["inv_cpu"].quantity
    initial_inv_mb_qty = sample_hardware["inv_mb"].quantity
    initial_order_count = db_session.query(Order).count()
    initial_cart_count = db_session.query(CartItem).count()
    initial_payment_count = db_session.query(Payment).count()

    # Perform compatibility check
    payload = {"product_ids": [cpu.id, mb.id]}
    response = client.post("/api/v1/compatibility/check", json=payload)
    assert response.status_code == 200

    # Refresh and assert unchanged
    db_session.expire_all()
    assert sample_hardware["inv_cpu"].quantity == initial_inv_cpu_qty
    assert sample_hardware["inv_mb"].quantity == initial_inv_mb_qty
    assert db_session.query(Order).count() == initial_order_count
    assert db_session.query(CartItem).count() == initial_cart_count
    assert db_session.query(Payment).count() == initial_payment_count
