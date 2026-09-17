from decimal import Decimal
import pytest
from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.inventory.models import (
    Inventory,
    InventoryTransaction,
    InventoryTransactionType,
)
from app.modules.products.models import Product, ProductStatus


@pytest.fixture
def test_category(db_session):
    cat = Category(name="Components", slug="components", is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def test_brand(db_session):
    brand = Brand(name="Acme Tech", slug="acme-tech", is_active=True)
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def test_product(db_session, test_category, test_brand):
    prod = Product(
        sku="INV-TEST-001",
        name="BuildTech Performance CPU",
        slug="buildtech-performance-cpu",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("299.99"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)
    return prod


def test_inventory_auto_creation_and_defaults(client, admin_auth_headers, test_product):
    """Test retrieving inventory for a new product initializes default fields."""
    res = client.get(f"/api/v1/inventory/{test_product.id}", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == test_product.id
    assert data["quantity"] == 0
    assert data["reserved_quantity"] == 0
    assert data["available_quantity"] == 0
    assert data["low_stock_threshold"] == 5
    assert data["availability_status"] == "OUT_OF_STOCK"


def test_admin_stock_in_success(client, admin_auth_headers, test_product, db_session):
    """Test stock-in increases inventory and logs an immutable audit transaction."""
    payload = {
        "quantity": 25,
        "reason": "Initial shipment arrival",
    }
    res = client.post(f"/api/v1/inventory/{test_product.id}/stock-in", json=payload, headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["quantity"] == 25
    assert data["available_quantity"] == 25
    assert data["availability_status"] == "IN_STOCK"

    # Verify transaction record
    tx_list = db_session.query(InventoryTransaction).filter(InventoryTransaction.product_id == test_product.id).all()
    assert len(tx_list) == 1
    assert tx_list[0].type == "STOCK_IN"
    assert tx_list[0].quantity_change == 25
    assert tx_list[0].quantity_before == 0
    assert tx_list[0].quantity_after == 25
    assert tx_list[0].reason == "Initial shipment arrival"


def test_customer_cannot_stock_in(client, customer_auth_headers, test_product):
    """Test customer user is forbidden (403) from managing stock."""
    payload = {"quantity": 10}
    res = client.post(f"/api/v1/inventory/{test_product.id}/stock-in", json=payload, headers=customer_auth_headers)
    assert res.status_code == 403


def test_unauthenticated_cannot_stock_in(client, test_product):
    """Test unauthenticated request is rejected (401)."""
    payload = {"quantity": 10}
    res = client.post(f"/api/v1/inventory/{test_product.id}/stock-in", json=payload)
    assert res.status_code == 401


def test_invalid_stock_in_quantity_rejected(client, admin_auth_headers, test_product):
    """Test stock-in rejects 0 or negative quantities."""
    res_zero = client.post(f"/api/v1/inventory/{test_product.id}/stock-in", json={"quantity": 0}, headers=admin_auth_headers)
    assert res_zero.status_code == 422

    res_neg = client.post(f"/api/v1/inventory/{test_product.id}/stock-in", json={"quantity": -5}, headers=admin_auth_headers)
    assert res_neg.status_code == 422


def test_inventory_adjustment_in_and_out(client, admin_auth_headers, test_product, db_session):
    """Test upward and downward manual stock adjustments with audit logging."""
    # 1. Set initial stock to 10 via stock-in
    client.post(f"/api/v1/inventory/{test_product.id}/stock-in", json={"quantity": 10}, headers=admin_auth_headers)

    # 2. Adjust Out 3 units (e.g. damaged)
    res_out = client.post(
        f"/api/v1/inventory/{test_product.id}/adjust",
        json={"type": "ADJUSTMENT_OUT", "quantity": 3, "reason": "Damaged in warehouse"},
        headers=admin_auth_headers,
    )
    assert res_out.status_code == 200
    assert res_out.json()["quantity"] == 7
    assert res_out.json()["available_quantity"] == 7

    # 3. Adjust In 5 units (e.g. found inventory)
    res_in = client.post(
        f"/api/v1/inventory/{test_product.id}/adjust",
        json={"type": "ADJUSTMENT_IN", "quantity": 5, "reason": "Recount adjustment"},
        headers=admin_auth_headers,
    )
    assert res_in.status_code == 200
    assert res_in.json()["quantity"] == 12

    # Check transactions count
    txs = db_session.query(InventoryTransaction).filter(InventoryTransaction.product_id == test_product.id).all()
    assert len(txs) == 3


def test_negative_stock_adjustment_rejected(client, admin_auth_headers, test_product, db_session):
    """Test reducing stock below 0 is rejected and quantity is unchanged."""
    client.post(f"/api/v1/inventory/{test_product.id}/stock-in", json={"quantity": 5}, headers=admin_auth_headers)

    # Attempt to reduce by 10
    res_excess = client.post(
        f"/api/v1/inventory/{test_product.id}/adjust",
        json={"type": "ADJUSTMENT_OUT", "quantity": 10, "reason": "Over-deduction attempt"},
        headers=admin_auth_headers,
    )
    assert res_excess.status_code == 400
    assert "below 0 units" in res_excess.json()["detail"]

    # Verify inventory is still 5
    inv = db_session.query(Inventory).filter(Inventory.product_id == test_product.id).first()
    assert inv.quantity == 5


def test_reserved_stock_protection(client, admin_auth_headers, test_product, db_session):
    """Test stock cannot be reduced below reserved quantity."""
    # Create inventory with qty=10, reserved=4
    inv = Inventory(product_id=test_product.id, quantity=10, reserved_quantity=4, low_stock_threshold=5)
    db_session.add(inv)
    db_session.commit()

    # Attempting to reduce 8 units (which would leave 2 < 4 reserved)
    res = client.post(
        f"/api/v1/inventory/{test_product.id}/adjust",
        json={"type": "ADJUSTMENT_OUT", "quantity": 8, "reason": "Attempting to exceed available"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 400
    assert "below reserved level" in res.json()["detail"]


def test_update_low_stock_threshold(client, admin_auth_headers, test_product):
    """Test updating low stock threshold."""
    res = client.patch(
        f"/api/v1/inventory/{test_product.id}/threshold",
        json={"low_stock_threshold": 8},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["low_stock_threshold"] == 8


def test_public_availability_states(client, admin_auth_headers, test_product, db_session):
    """Test OUT_OF_STOCK, LOW_STOCK, and IN_STOCK public status calculations."""
    # 1. Zero quantity -> OUT_OF_STOCK
    res_zero = client.get(f"/api/v1/products/{test_product.id}/availability")
    assert res_zero.status_code == 200
    assert res_zero.json()["availability"] == "OUT_OF_STOCK"
    assert res_zero.json()["is_available"] is False

    # 2. Add 4 units (threshold is 5) -> LOW_STOCK
    client.post(f"/api/v1/inventory/{test_product.id}/stock-in", json={"quantity": 4}, headers=admin_auth_headers)
    res_low = client.get(f"/api/v1/products/{test_product.id}/availability")
    assert res_low.status_code == 200
    assert res_low.json()["availability"] == "LOW_STOCK"
    assert res_low.json()["is_available"] is True

    # 3. Add 10 more units (total 14 > 5) -> IN_STOCK
    client.post(f"/api/v1/inventory/{test_product.id}/stock-in", json={"quantity": 10}, headers=admin_auth_headers)
    res_in = client.get(f"/api/v1/products/{test_product.id}/availability")
    assert res_in.status_code == 200
    assert res_in.json()["availability"] == "IN_STOCK"
    assert res_in.json()["is_available"] is True


def test_public_cannot_view_draft_product_availability(client, test_category, test_brand, db_session):
    """Test public request for draft product availability returns 404."""
    draft_prod = Product(
        sku="DRAFT-AVAIL",
        name="Hidden Draft Item",
        slug="hidden-draft-item",
        category_id=test_category.id,
        brand_id=test_brand.id,
        price=Decimal("199.00"),
        status=ProductStatus.DRAFT.value,
        is_active=True,
    )
    db_session.add(draft_prod)
    db_session.commit()

    res = client.get(f"/api/v1/products/{draft_prod.id}/availability")
    assert res.status_code == 404


def test_transaction_history_ordered_newest_first(client, admin_auth_headers, test_product):
    """Test transaction history returns newest entries first."""
    client.post(f"/api/v1/inventory/{test_product.id}/stock-in", json={"quantity": 10, "reason": "First"}, headers=admin_auth_headers)
    client.post(f"/api/v1/inventory/{test_product.id}/stock-in", json={"quantity": 20, "reason": "Second"}, headers=admin_auth_headers)
    client.post(f"/api/v1/inventory/{test_product.id}/adjust", json={"type": "ADJUSTMENT_OUT", "quantity": 5, "reason": "Third"}, headers=admin_auth_headers)

    res = client.get(f"/api/v1/inventory/{test_product.id}/transactions", headers=admin_auth_headers)
    assert res.status_code == 200
    txs = res.json()
    assert len(txs) == 3
    assert txs[0]["reason"] == "Third"
    assert txs[1]["reason"] == "Second"
    assert txs[2]["reason"] == "First"


def test_admin_list_inventory_with_search_and_filters(client, admin_auth_headers, test_category, test_brand, db_session):
    """Test admin list inventory endpoint with search and availability filters."""
    p1 = Product(sku="SKU-AAA", name="Alpha GPU", slug="alpha-gpu", category_id=test_category.id, brand_id=test_brand.id, price=Decimal("100"), status=ProductStatus.ACTIVE.value, is_active=True)
    p2 = Product(sku="SKU-BBB", name="Beta CPU", slug="beta-cpu", category_id=test_category.id, brand_id=test_brand.id, price=Decimal("200"), status=ProductStatus.ACTIVE.value, is_active=True)
    db_session.add_all([p1, p2])
    db_session.commit()

    # Stock in for p1 only
    client.post(f"/api/v1/inventory/{p1.id}/stock-in", json={"quantity": 50}, headers=admin_auth_headers)

    # Search by keyword
    res_search = client.get("/api/v1/inventory?search=Alpha", headers=admin_auth_headers)
    assert len(res_search.json()) == 1
    assert res_search.json()[0]["product"]["sku"] == "SKU-AAA"

    # Filter by availability IN_STOCK
    res_in_stock = client.get("/api/v1/inventory?availability=IN_STOCK", headers=admin_auth_headers)
    skus_in_stock = [item["product"]["sku"] for item in res_in_stock.json()]
    assert "SKU-AAA" in skus_in_stock
    assert "SKU-BBB" not in skus_in_stock


def test_product_deletion_cascades_to_inventory_and_transactions(client, admin_auth_headers, test_product, db_session):
    """Test deleting a product removes its inventory and audit transactions."""
    client.post(f"/api/v1/inventory/{test_product.id}/stock-in", json={"quantity": 10}, headers=admin_auth_headers)

    # Delete product
    res = client.delete(f"/api/v1/products/{test_product.id}", headers=admin_auth_headers)
    assert res.status_code == 200

    # Verify inventory and transactions are deleted
    assert db_session.query(Inventory).filter(Inventory.product_id == test_product.id).first() is None
    assert db_session.query(InventoryTransaction).filter(InventoryTransaction.product_id == test_product.id).count() == 0
