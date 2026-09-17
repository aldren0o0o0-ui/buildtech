from decimal import Decimal
import pytest
from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.products.models import Product, ProductStatus
from app.modules.products.specifications.models import (
    CaseSpecification,
    CoolingSpecification,
    CpuSpecification,
    GpuSpecification,
    MemorySpecification,
    MotherboardSpecification,
    PsuSpecification,
    StorageSpecification,
)


@pytest.fixture
def cpu_category(db_session):
    cat = Category(name="Processors", slug="cpu", is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def gpu_category(db_session):
    cat = Category(name="Graphics Cards", slug="gpu", is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def motherboard_category(db_session):
    cat = Category(name="Motherboards", slug="motherboard", is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def memory_category(db_session):
    cat = Category(name="Memory (RAM)", slug="memory", is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def storage_category(db_session):
    cat = Category(name="Storage Drives", slug="storage", is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def psu_category(db_session):
    cat = Category(name="Power Supplies", slug="psu", is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def case_category(db_session):
    cat = Category(name="PC Cases", slug="case", is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def cooling_category(db_session):
    cat = Category(name="CPU Coolers", slug="cooling", is_active=True)
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat


@pytest.fixture
def test_brand(db_session):
    brand = Brand(name="Test Brand", slug="test-brand", is_active=True)
    db_session.add(brand)
    db_session.commit()
    db_session.refresh(brand)
    return brand


@pytest.fixture
def cpu_product(db_session, cpu_category, test_brand):
    prod = Product(
        sku="CPU-7800X3D",
        name="AMD Ryzen 7 7800X3D",
        slug="amd-ryzen-7-7800x3d",
        category_id=cpu_category.id,
        brand_id=test_brand.id,
        price=Decimal("449.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)
    return prod


@pytest.fixture
def gpu_product(db_session, gpu_category, test_brand):
    prod = Product(
        sku="GPU-4070S",
        name="NVIDIA RTX 4070 Super",
        slug="nvidia-rtx-4070-super",
        category_id=gpu_category.id,
        brand_id=test_brand.id,
        price=Decimal("599.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(prod)
    db_session.commit()
    db_session.refresh(prod)
    return prod


def test_public_read_active_product_specifications(client, cpu_product, db_session):
    """Test public can read specifications for an active product."""
    cpu_spec = CpuSpecification(
        product_id=cpu_product.id,
        socket="AM5",
        core_count=8,
        thread_count=16,
        base_clock_ghz=Decimal("4.20"),
        boost_clock_ghz=Decimal("5.00"),
        tdp_watts=120,
        architecture="Zen 4",
        integrated_graphics="Radeon Graphics",
    )
    db_session.add(cpu_spec)
    db_session.commit()

    res = client.get(f"/api/v1/products/{cpu_product.id}/specifications")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "CPU"
    assert data["data"]["socket"] == "AM5"
    assert data["data"]["core_count"] == 8


def test_public_cannot_read_draft_product_specifications(client, cpu_category, test_brand, db_session):
    """Test public user cannot access specifications of a draft product."""
    draft_prod = Product(
        sku="CPU-DRAFT",
        name="Unreleased CPU",
        slug="unreleased-cpu",
        category_id=cpu_category.id,
        brand_id=test_brand.id,
        price=Decimal("999.00"),
        status=ProductStatus.DRAFT.value,
        is_active=True,
    )
    db_session.add(draft_prod)
    db_session.commit()
    db_session.refresh(draft_prod)

    res = client.get(f"/api/v1/products/{draft_prod.id}/specifications")
    assert res.status_code == 404


def test_admin_can_read_draft_product_specifications(client, admin_auth_headers, cpu_category, test_brand, db_session):
    """Test admin can read specifications of a draft product."""
    draft_prod = Product(
        sku="CPU-DRAFT-2",
        name="Unreleased CPU 2",
        slug="unreleased-cpu-2",
        category_id=cpu_category.id,
        brand_id=test_brand.id,
        price=Decimal("999.00"),
        status=ProductStatus.DRAFT.value,
        is_active=True,
    )
    db_session.add(draft_prod)
    db_session.commit()
    db_session.refresh(draft_prod)

    res = client.get(f"/api/v1/products/{draft_prod.id}/specifications?include_inactive=true", headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["type"] == "CPU"


def test_customer_cannot_update_specifications(client, customer_auth_headers, cpu_product):
    """Test customer role is forbidden (403) from updating specifications."""
    payload = {
        "socket": "AM5",
        "core_count": 8,
        "thread_count": 16,
        "base_clock_ghz": "4.20",
        "boost_clock_ghz": "5.00",
        "tdp_watts": 120,
    }
    res = client.put(f"/api/v1/products/{cpu_product.id}/specifications", json=payload, headers=customer_auth_headers)
    assert res.status_code == 403


def test_unauthenticated_cannot_update_specifications(client, cpu_product):
    """Test unauthenticated request is rejected (401)."""
    payload = {
        "socket": "AM5",
        "core_count": 8,
        "thread_count": 16,
        "base_clock_ghz": "4.20",
        "boost_clock_ghz": "5.00",
        "tdp_watts": 120,
    }
    res = client.put(f"/api/v1/products/{cpu_product.id}/specifications", json=payload)
    assert res.status_code == 401


def test_upsert_cpu_specifications(client, admin_auth_headers, cpu_product, db_session):
    """Test creating and updating CPU specifications (UPSERT)."""
    # 1. Create
    payload = {
        "socket": "AM5",
        "core_count": 8,
        "thread_count": 16,
        "base_clock_ghz": "4.20",
        "boost_clock_ghz": "5.00",
        "tdp_watts": 120,
        "architecture": "Zen 4",
        "integrated_graphics": "Radeon Graphics",
    }
    res_create = client.put(f"/api/v1/products/{cpu_product.id}/specifications", json=payload, headers=admin_auth_headers)
    assert res_create.status_code == 200
    assert res_create.json()["type"] == "CPU"
    assert res_create.json()["data"]["socket"] == "AM5"

    # Verify only 1 row exists
    count = db_session.query(CpuSpecification).filter(CpuSpecification.product_id == cpu_product.id).count()
    assert count == 1

    # 2. Update existing
    payload["boost_clock_ghz"] = "5.05"
    res_update = client.put(f"/api/v1/products/{cpu_product.id}/specifications", json=payload, headers=admin_auth_headers)
    assert res_update.status_code == 200
    assert float(res_update.json()["data"]["boost_clock_ghz"]) == 5.05

    # Count remains 1
    count = db_session.query(CpuSpecification).filter(CpuSpecification.product_id == cpu_product.id).count()
    assert count == 1


def test_cpu_specification_rejected_for_gpu_product(client, admin_auth_headers, gpu_product):
    """Test that attempting to save CPU specifications for a GPU product returns 400."""
    payload = {
        "type": "CPU",
        "socket": "AM5",
        "core_count": 8,
        "thread_count": 16,
        "base_clock_ghz": "4.20",
        "boost_clock_ghz": "5.00",
        "tdp_watts": 120,
    }
    res = client.put(f"/api/v1/products/{gpu_product.id}/specifications", json=payload, headers=admin_auth_headers)
    assert res.status_code == 400
    assert "Mismatched specification type" in res.json()["detail"]


def test_invalid_cpu_core_count_rejected(client, admin_auth_headers, cpu_product):
    """Test schema validation rejects 0 or negative core count."""
    payload = {
        "socket": "AM5",
        "core_count": 0,
        "thread_count": 16,
        "base_clock_ghz": "4.20",
        "boost_clock_ghz": "5.00",
        "tdp_watts": 120,
    }
    res = client.put(f"/api/v1/products/{cpu_product.id}/specifications", json=payload, headers=admin_auth_headers)
    assert res.status_code == 422


def test_upsert_gpu_specifications(client, admin_auth_headers, gpu_product):
    """Test creating and validating GPU specifications."""
    payload = {
        "chipset": "AD104",
        "vram_gb": 12,
        "memory_type": "GDDR6X",
        "core_clock_mhz": 1980,
        "boost_clock_mhz": 2475,
        "length_mm": 242,
        "tdp_watts": 220,
        "recommended_psu_watts": 650,
    }
    res = client.put(f"/api/v1/products/{gpu_product.id}/specifications", json=payload, headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["type"] == "GPU"
    assert res.json()["data"]["vram_gb"] == 12


def test_motherboard_specifications(client, admin_auth_headers, motherboard_category, test_brand, db_session):
    """Test Motherboard specifications."""
    mb_prod = Product(
        sku="MB-B650",
        name="MSI MAG B650 Tomahawk WiFi",
        slug="msi-mag-b650-tomahawk-wifi",
        category_id=motherboard_category.id,
        brand_id=test_brand.id,
        price=Decimal("219.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(mb_prod)
    db_session.commit()

    payload = {
        "socket": "AM5",
        "chipset": "B650",
        "form_factor": "ATX",
        "memory_type": "DDR5",
        "memory_slots": 4,
        "max_memory_gb": 192,
        "pcie_version": "PCIe 4.0",
        "wifi": True,
    }
    res = client.put(f"/api/v1/products/{mb_prod.id}/specifications", json=payload, headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["wifi"] is True


def test_memory_specifications(client, admin_auth_headers, memory_category, test_brand, db_session):
    """Test Memory specifications."""
    ram_prod = Product(
        sku="RAM-32GB",
        name="Corsair Vengeance 32GB DDR5 6000",
        slug="corsair-vengeance-32gb-ddr5-6000",
        category_id=memory_category.id,
        brand_id=test_brand.id,
        price=Decimal("119.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(ram_prod)
    db_session.commit()

    payload = {
        "memory_type": "DDR5",
        "capacity_gb": 32,
        "speed_mhz": 6000,
        "module_count": 2,
        "cas_latency": 30,
    }
    res = client.put(f"/api/v1/products/{ram_prod.id}/specifications", json=payload, headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["speed_mhz"] == 6000


def test_storage_specifications(client, admin_auth_headers, storage_category, test_brand, db_session):
    """Test Storage specifications."""
    ssd_prod = Product(
        sku="SSD-2TB",
        name="Samsung 990 Pro 2TB",
        slug="samsung-990-pro-2tb",
        category_id=storage_category.id,
        brand_id=test_brand.id,
        price=Decimal("179.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(ssd_prod)
    db_session.commit()

    payload = {
        "storage_type": "SSD",
        "capacity_gb": 2000,
        "interface": "PCIe 4.0 NVMe",
        "form_factor": "M.2 2280",
        "read_speed_mbps": 7450,
        "write_speed_mbps": 6900,
    }
    res = client.put(f"/api/v1/products/{ssd_prod.id}/specifications", json=payload, headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["capacity_gb"] == 2000


def test_psu_specifications(client, admin_auth_headers, psu_category, test_brand, db_session):
    """Test PSU specifications."""
    psu_prod = Product(
        sku="PSU-850W",
        name="Corsair RM850x",
        slug="corsair-rm850x",
        category_id=psu_category.id,
        brand_id=test_brand.id,
        price=Decimal("139.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(psu_prod)
    db_session.commit()

    payload = {
        "wattage": 850,
        "efficiency_rating": "80+ Gold",
        "modularity": "Full Modular",
        "form_factor": "ATX",
    }
    res = client.put(f"/api/v1/products/{psu_prod.id}/specifications", json=payload, headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["wattage"] == 850


def test_case_specifications(client, admin_auth_headers, case_category, test_brand, db_session):
    """Test Case specifications."""
    case_prod = Product(
        sku="CASE-4000D",
        name="Corsair 4000D Airflow",
        slug="corsair-4000d-airflow",
        category_id=case_category.id,
        brand_id=test_brand.id,
        price=Decimal("104.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(case_prod)
    db_session.commit()

    payload = {
        "case_type": "Mid Tower",
        "supported_motherboard_form_factors": ["ATX", "Micro-ATX", "Mini-ITX"],
        "max_gpu_length_mm": 360,
        "max_cpu_cooler_height_mm": 170,
        "psu_form_factor": "ATX",
        "drive_bays": "2x 3.5, 2x 2.5",
    }
    res = client.put(f"/api/v1/products/{case_prod.id}/specifications", json=payload, headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["max_gpu_length_mm"] == 360


def test_cooling_specifications(client, admin_auth_headers, cooling_category, test_brand, db_session):
    """Test Cooling specifications."""
    cooler_prod = Product(
        sku="COOLER-AK620",
        name="DeepCool AK620",
        slug="deepcool-ak620",
        category_id=cooling_category.id,
        brand_id=test_brand.id,
        price=Decimal("64.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    db_session.add(cooler_prod)
    db_session.commit()

    payload = {
        "cooler_type": "AIR",
        "supported_sockets": ["AM5", "AM4", "LGA1700", "LGA1200"],
        "fan_size_mm": 120,
        "max_tdp_watts": 260,
        "height_mm": 160,
    }
    res = client.put(f"/api/v1/products/{cooler_prod.id}/specifications", json=payload, headers=admin_auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["height_mm"] == 160


def test_delete_specifications_keeps_product(client, admin_auth_headers, cpu_product, db_session):
    """Test deleting specifications removes the spec row without deleting the product."""
    cpu_spec = CpuSpecification(
        product_id=cpu_product.id,
        socket="AM5",
        core_count=8,
        thread_count=16,
        base_clock_ghz=Decimal("4.20"),
        boost_clock_ghz=Decimal("5.00"),
        tdp_watts=120,
    )
    db_session.add(cpu_spec)
    db_session.commit()

    res = client.delete(f"/api/v1/products/{cpu_product.id}/specifications", headers=admin_auth_headers)
    assert res.status_code == 200
    assert "deleted successfully" in res.json()["message"]

    # Spec row is deleted
    assert db_session.query(CpuSpecification).filter(CpuSpecification.product_id == cpu_product.id).first() is None
    # Product still exists
    assert db_session.query(Product).filter(Product.id == cpu_product.id).first() is not None


def test_deleting_product_cascades_to_specification(client, admin_auth_headers, cpu_product, db_session):
    """Test that deleting a Product automatically removes its specification row."""
    cpu_spec = CpuSpecification(
        product_id=cpu_product.id,
        socket="AM5",
        core_count=8,
        thread_count=16,
        base_clock_ghz=Decimal("4.20"),
        boost_clock_ghz=Decimal("5.00"),
        tdp_watts=120,
    )
    db_session.add(cpu_spec)
    db_session.commit()

    # Delete product via admin API
    res = client.delete(f"/api/v1/products/{cpu_product.id}", headers=admin_auth_headers)
    assert res.status_code == 200

    # Specification row is also removed
    assert db_session.query(CpuSpecification).filter(CpuSpecification.product_id == cpu_product.id).first() is None
