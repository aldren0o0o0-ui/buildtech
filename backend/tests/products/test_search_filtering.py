from decimal import Decimal
import pytest

from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.inventory.models import Inventory
from app.modules.products.models import Product, ProductStatus
from app.modules.products.specifications.models import (
    CaseSpecification,
    CpuSpecification,
    GpuSpecification,
    MemorySpecification,
    MotherboardSpecification,
    PsuSpecification,
    StorageSpecification,
)


@pytest.fixture
def catalog_setup(db_session):
    """Creates a realistic hardware catalog with categories, brands, specs, and inventory."""
    # Categories
    cpu_cat = Category(name="Processors", slug="cpu", is_active=True)
    gpu_cat = Category(name="Graphics Cards", slug="gpu", is_active=True)
    mb_cat = Category(name="Motherboards", slug="motherboard", is_active=True)
    ram_cat = Category(name="Memory", slug="memory", is_active=True)
    ssd_cat = Category(name="Storage", slug="storage", is_active=True)
    psu_cat = Category(name="Power Supplies", slug="psu", is_active=True)

    # Brands
    amd_brand = Brand(name="AMD", slug="amd", is_active=True)
    intel_brand = Brand(name="Intel", slug="intel", is_active=True)
    nvidia_brand = Brand(name="NVIDIA", slug="nvidia", is_active=True)
    corsair_brand = Brand(name="Corsair", slug="corsair", is_active=True)
    asus_brand = Brand(name="ASUS", slug="asus", is_active=True)

    db_session.add_all([
        cpu_cat, gpu_cat, mb_cat, ram_cat, ssd_cat, psu_cat,
        amd_brand, intel_brand, nvidia_brand, corsair_brand, asus_brand,
    ])
    db_session.commit()

    # Products:
    # 1. AMD Ryzen 7 7800X3D (CPU, AM5, 8 cores, 16 threads, 120W)
    p_ryzen7 = Product(
        sku="CPU-AMD-7800X3D",
        name="AMD Ryzen 7 7800X3D",
        slug="amd-ryzen-7-7800x3d",
        description="Ultimate gaming processor with 3D V-Cache technology.",
        category_id=cpu_cat.id,
        brand_id=amd_brand.id,
        price=Decimal("449.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 2. AMD Ryzen 5 7600 (CPU, AM5, 6 cores, 12 threads, 65W)
    p_ryzen5 = Product(
        sku="CPU-AMD-7600",
        name="AMD Ryzen 5 7600",
        slug="amd-ryzen-5-7600",
        description="Budget 6-core AM5 gaming processor.",
        category_id=cpu_cat.id,
        brand_id=amd_brand.id,
        price=Decimal("199.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 3. Intel Core i7-14700K (CPU, LGA1700, 20 cores, 28 threads, 253W)
    p_intel = Product(
        sku="CPU-INTEL-14700K",
        name="Intel Core i7-14700K",
        slug="intel-core-i7-14700k",
        description="High performance hybrid architecture processor.",
        category_id=cpu_cat.id,
        brand_id=intel_brand.id,
        price=Decimal("389.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 4. NVIDIA GeForce RTX 4080 Super (GPU, 16GB VRAM, GDDR6X)
    p_rtx4080 = Product(
        sku="GPU-NV-4080S",
        name="NVIDIA GeForce RTX 4080 Super",
        slug="nvidia-geforce-rtx-4080-super",
        description="4K Ray Tracing gaming GPU with DLSS 3.",
        category_id=gpu_cat.id,
        brand_id=nvidia_brand.id,
        price=Decimal("999.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 5. ASUS ROG Strix B650E-F (Motherboard, AM5, ATX, DDR5, WiFi)
    p_mb_asus = Product(
        sku="MB-ASUS-B650E",
        name="ASUS ROG Strix B650E-F Gaming WiFi",
        slug="asus-rog-strix-b650e-f",
        description="Premium AM5 ATX gaming motherboard.",
        category_id=mb_cat.id,
        brand_id=asus_brand.id,
        price=Decimal("269.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 6. Corsair Vengeance 32GB DDR5 (RAM, DDR5, 32GB, 6000MHz)
    p_ram = Product(
        sku="RAM-COR-DDR5-32",
        name="Corsair Vengeance 32GB DDR5-6000",
        slug="corsair-vengeance-32gb-ddr5",
        description="High-speed dual-channel DDR5 memory kit.",
        category_id=ram_cat.id,
        brand_id=corsair_brand.id,
        price=Decimal("119.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 7. Corsair RM850x (PSU, 850W, 80 Plus Gold, Full Modular)
    p_psu = Product(
        sku="PSU-COR-850",
        name="Corsair RM850x 850W",
        slug="corsair-rm850x-850w",
        description="Ultra-quiet fully modular 850-watt power supply.",
        category_id=psu_cat.id,
        brand_id=corsair_brand.id,
        price=Decimal("139.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 8. Draft Product (should never show on public storefront)
    p_draft = Product(
        sku="CPU-SECRET-UNRELEASED",
        name="Unreleased Secret CPU",
        slug="unreleased-secret-cpu",
        description="Confidential next-gen processor.",
        category_id=cpu_cat.id,
        brand_id=amd_brand.id,
        price=Decimal("799.00"),
        status=ProductStatus.DRAFT.value,
        is_active=True,
    )

    db_session.add_all([
        p_ryzen7, p_ryzen5, p_intel, p_rtx4080, p_mb_asus, p_ram, p_psu, p_draft,
    ])
    db_session.commit()

    # Specifications
    cpu1_spec = CpuSpecification(
        product_id=p_ryzen7.id,
        socket="AM5",
        core_count=8,
        thread_count=16,
        base_clock_ghz=Decimal("4.20"),
        boost_clock_ghz=Decimal("5.00"),
        tdp_watts=120,
    )
    cpu2_spec = CpuSpecification(
        product_id=p_ryzen5.id,
        socket="AM5",
        core_count=6,
        thread_count=12,
        base_clock_ghz=Decimal("3.80"),
        boost_clock_ghz=Decimal("5.10"),
        tdp_watts=65,
    )
    cpu3_spec = CpuSpecification(
        product_id=p_intel.id,
        socket="LGA1700",
        core_count=20,
        thread_count=28,
        base_clock_ghz=Decimal("3.40"),
        boost_clock_ghz=Decimal("5.60"),
        tdp_watts=253,
    )
    gpu_spec = GpuSpecification(
        product_id=p_rtx4080.id,
        chipset="GeForce RTX 4080 Super",
        vram_gb=16,
        memory_type="GDDR6X",
        boost_clock_mhz=2550,
        length_mm=304,
        tdp_watts=320,
        recommended_psu_watts=750,
    )
    mb_spec = MotherboardSpecification(
        product_id=p_mb_asus.id,
        socket="AM5",
        chipset="AMD B650E",
        form_factor="ATX",
        memory_type="DDR5",
        memory_slots=4,
        max_memory_gb=128,
        wifi=True,
    )
    ram_spec = MemorySpecification(
        product_id=p_ram.id,
        memory_type="DDR5",
        capacity_gb=32,
        speed_mhz=6000,
        module_count=2,
    )
    psu_spec = PsuSpecification(
        product_id=p_psu.id,
        wattage=850,
        efficiency_rating="80 Plus Gold",
        modularity="Full",
        form_factor="ATX",
    )
    db_session.add_all([
        cpu1_spec, cpu2_spec, cpu3_spec, gpu_spec, mb_spec, ram_spec, psu_spec,
    ])

    # Inventory
    inv_ryzen7 = Inventory(product_id=p_ryzen7.id, quantity=10, reserved_quantity=0)
    inv_ryzen5 = Inventory(product_id=p_ryzen5.id, quantity=5, reserved_quantity=0)
    inv_intel = Inventory(product_id=p_intel.id, quantity=0, reserved_quantity=0)  # Out of stock
    inv_rtx = Inventory(product_id=p_rtx4080.id, quantity=4, reserved_quantity=0)
    inv_mb = Inventory(product_id=p_mb_asus.id, quantity=8, reserved_quantity=0)
    inv_ram = Inventory(product_id=p_ram.id, quantity=15, reserved_quantity=0)
    inv_psu = Inventory(product_id=p_psu.id, quantity=12, reserved_quantity=0)
    db_session.add_all([
        inv_ryzen7, inv_ryzen5, inv_intel, inv_rtx, inv_mb, inv_ram, inv_psu,
    ])
    db_session.commit()

    return {
        "categories": {"cpu": cpu_cat, "gpu": gpu_cat, "mb": mb_cat},
        "brands": {"amd": amd_brand, "intel": intel_brand, "nvidia": nvidia_brand},
        "products": {
            "ryzen7": p_ryzen7,
            "ryzen5": p_ryzen5,
            "intel": p_intel,
            "rtx4080": p_rtx4080,
            "mb": p_mb_asus,
            "ram": p_ram,
            "psu": p_psu,
            "draft": p_draft,
        },
    }


# =========================================================================
# 1. SEARCH TESTS
# =========================================================================

def test_search_by_product_name(client, catalog_setup):
    res = client.get("/api/v1/products?search=ryzen")
    assert res.status_code == 200
    skus = [p["sku"] for p in res.json()]
    assert "CPU-AMD-7800X3D" in skus
    assert "CPU-AMD-7600" in skus
    assert "CPU-INTEL-14700K" not in skus


def test_search_by_sku(client, catalog_setup):
    res = client.get("/api/v1/products?search=4080S")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["sku"] == "GPU-NV-4080S"


def test_search_case_insensitive_and_partial(client, catalog_setup):
    res = client.get("/api/v1/products?search=rYzEn 7")
    assert res.status_code == 200
    skus = [p["sku"] for p in res.json()]
    assert "CPU-AMD-7800X3D" in skus
    assert "CPU-AMD-7600" not in skus


def test_search_by_brand_and_category_text(client, catalog_setup):
    # Search for "NVIDIA" should match via Brand.name
    res = client.get("/api/v1/products?search=nvidia")
    assert res.status_code == 200
    skus = [p["sku"] for p in res.json()]
    assert "GPU-NV-4080S" in skus

    # Search for "Motherboards" matches via Category.name
    res_cat = client.get("/api/v1/products?search=motherboard")
    assert res_cat.status_code == 200
    skus_cat = [p["sku"] for p in res_cat.json()]
    assert "MB-ASUS-B650E" in skus_cat


def test_empty_and_whitespace_search(client, catalog_setup):
    res = client.get("/api/v1/products?search=   ")
    assert res.status_code == 200
    # Should not filter out everything
    assert len(res.json()) == 7


# =========================================================================
# 2. CATEGORY & BRAND FILTER TESTS
# =========================================================================

def test_category_filter_by_slug_and_id(client, catalog_setup):
    # Filter by slug
    res_slug = client.get("/api/v1/products?category=cpu")
    assert res_slug.status_code == 200
    assert len(res_slug.json()) == 3  # ryzen7, ryzen5, intel (draft excluded)

    # Filter by category_id
    cpu_id = catalog_setup["categories"]["cpu"].id
    res_id = client.get(f"/api/v1/products?category_id={cpu_id}")
    assert res_id.status_code == 200
    assert len(res_id.json()) == 3


def test_brand_filter_by_slug_and_id(client, catalog_setup):
    # Filter by slug
    res_slug = client.get("/api/v1/products?brand=amd")
    assert res_slug.status_code == 200
    assert len(res_slug.json()) == 2  # ryzen7, ryzen5

    # Filter by brand_id
    amd_id = catalog_setup["brands"]["amd"].id
    res_id = client.get(f"/api/v1/products?brand_id={amd_id}")
    assert res_id.status_code == 200
    assert len(res_id.json()) == 2


# =========================================================================
# 3. PRICE RANGE FILTER TESTS & VALIDATION
# =========================================================================

def test_price_range_filtering(client, catalog_setup):
    # Products between $200 and $450
    res = client.get("/api/v1/products?min_price=200&max_price=450")
    assert res.status_code == 200
    skus = [p["sku"] for p in res.json()]
    assert "CPU-AMD-7800X3D" in skus  # 449.00
    assert "CPU-INTEL-14700K" in skus  # 389.00
    assert "MB-ASUS-B650E" in skus     # 269.00
    assert "CPU-AMD-7600" not in skus  # 199.00
    assert "GPU-NV-4080S" not in skus  # 999.00


def test_invalid_price_range_rejected(client, catalog_setup):
    # min_price > max_price
    res_inverted = client.get("/api/v1/products?min_price=500&max_price=200")
    assert res_inverted.status_code == 400
    assert "cannot exceed" in res_inverted.json()["detail"].lower()

    # negative min_price
    res_neg = client.get("/api/v1/products?min_price=-10")
    assert res_neg.status_code in (400, 422)


# =========================================================================
# 4. SORTING TESTS
# =========================================================================

def test_sorting_modes(client, catalog_setup):
    # Price ASC
    res_asc = client.get("/api/v1/products?sort=price_asc")
    assert res_asc.status_code == 200
    prices = [Decimal(str(p["price"])) for p in res_asc.json()]
    assert prices == sorted(prices)

    # Price DESC
    res_desc = client.get("/api/v1/products?sort=price_desc")
    assert res_desc.status_code == 200
    prices_desc = [Decimal(str(p["price"])) for p in res_desc.json()]
    assert prices_desc == sorted(prices_desc, reverse=True)

    # Name ASC
    res_name = client.get("/api/v1/products?sort=name_asc")
    assert res_name.status_code == 200
    names = [p["name"] for p in res_name.json()]
    assert names == sorted(names)


def test_invalid_sort_parameter_rejected(client, catalog_setup):
    res = client.get("/api/v1/products?sort=invalid_mode")
    assert res.status_code == 400
    assert "invalid sort option" in res.json()["detail"].lower()


# =========================================================================
# 5. SERVER-SIDE PAGINATION TESTS
# =========================================================================

def test_server_side_pagination(client, catalog_setup):
    # Request page 1 with page_size 3
    res_p1 = client.get("/api/v1/products?page=1&page_size=3")
    assert res_p1.status_code == 200
    data_p1 = res_p1.json()

    assert "items" in data_p1
    assert data_p1["total"] == 7
    assert data_p1["page"] == 1
    assert data_p1["page_size"] == 3
    assert data_p1["total_pages"] == 3
    assert len(data_p1["items"]) == 3

    # Request page 2
    res_p2 = client.get("/api/v1/products?page=2&page_size=3")
    assert res_p2.status_code == 200
    data_p2 = res_p2.json()
    assert data_p2["page"] == 2
    assert len(data_p2["items"]) == 3
    # Items on page 1 and page 2 must be distinct
    p1_ids = {p["id"] for p in data_p1["items"]}
    p2_ids = {p["id"] for p in data_p2["items"]}
    assert p1_ids.isdisjoint(p2_ids)


def test_invalid_pagination_parameters(client, catalog_setup):
    # page < 1
    res = client.get("/api/v1/products?page=0")
    assert res.status_code in (400, 422)

    # page_size > 100
    res_max = client.get("/api/v1/products?page=1&page_size=500")
    assert res_max.status_code in (400, 422)


# =========================================================================
# 6. SPECIFICATION FILTERING TESTS
# =========================================================================

def test_filter_cpu_socket_and_cores(client, catalog_setup):
    # Sockets = AM5
    res = client.get("/api/v1/products?category=cpu&socket=AM5")
    assert res.status_code == 200
    skus = [p["sku"] for p in res.json()]
    assert "CPU-AMD-7800X3D" in skus
    assert "CPU-AMD-7600" in skus
    assert "CPU-INTEL-14700K" not in skus

    # AM5 with at least 8 cores
    res_cores = client.get("/api/v1/products?category=cpu&socket=AM5&cores_min=8")
    assert res_cores.status_code == 200
    skus_cores = [p["sku"] for p in res_cores.json()]
    assert "CPU-AMD-7800X3D" in skus_cores
    assert "CPU-AMD-7600" not in skus_cores


def test_filter_gpu_vram(client, catalog_setup):
    # GPU with at least 16GB VRAM
    res = client.get("/api/v1/products?category=gpu&vram_min=16")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["sku"] == "GPU-NV-4080S"

    # GPU with 24GB VRAM (none in catalog)
    res_24 = client.get("/api/v1/products?category=gpu&vram_min=24")
    assert res_24.status_code == 200
    assert len(res_24.json()) == 0


def test_filter_motherboard_socket_and_form_factor(client, catalog_setup):
    res = client.get("/api/v1/products?category=motherboard&socket=AM5&form_factor=ATX")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["sku"] == "MB-ASUS-B650E"


def test_filter_ram_specifications(client, catalog_setup):
    res = client.get("/api/v1/products?category=memory&memory_type=DDR5&capacity_min=32")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["sku"] == "RAM-COR-DDR5-32"


def test_filter_psu_wattage(client, catalog_setup):
    res = client.get("/api/v1/products?category=psu&wattage_min=800")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["sku"] == "PSU-COR-850"


def test_specification_queries_produce_no_duplicates(client, catalog_setup):
    """
    Verifies that joining / subquerying multiple specifications
    never yields duplicate product rows in the result set.
    """
    res = client.get("/api/v1/products?socket=AM5")
    assert res.status_code == 200
    items = res.json()
    ids = [p["id"] for p in items]
    assert len(ids) == len(set(ids))  # All IDs must be strictly unique


# =========================================================================
# 7. INVENTORY AVAILABILITY & VISIBILITY TESTS
# =========================================================================

def test_filter_in_stock_products_only(client, catalog_setup):
    # In stock only
    res_instock = client.get("/api/v1/products?category=cpu&in_stock=true")
    assert res_instock.status_code == 200
    skus = [p["sku"] for p in res_instock.json()]
    assert "CPU-AMD-7800X3D" in skus  # qty 10
    assert "CPU-AMD-7600" in skus      # qty 5
    assert "CPU-INTEL-14700K" not in skus  # qty 0 (out of stock)


def test_draft_products_excluded_from_public_search(client, catalog_setup):
    # Search for "unreleased"
    res = client.get("/api/v1/products?search=unreleased")
    assert res.status_code == 200
    assert len(res.json()) == 0


# =========================================================================
# 8. COMBINED MULTI-FILTER COMPOSABILITY TEST
# =========================================================================

def test_combined_search_category_brand_price_sort_paginate(client, catalog_setup):
    """
    Simulates a realistic storefront user flow:
    Search term + category + brand + price range + sort + pagination.
    """
    res = client.get(
        "/api/v1/products"
        "?search=ryzen"
        "&category=cpu"
        "&brand=amd"
        "&min_price=150"
        "&max_price=500"
        "&socket=AM5"
        "&sort=price_asc"
        "&page=1"
        "&page_size=10"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2
    assert data["items"][0]["sku"] == "CPU-AMD-7600"       # $199.00
    assert data["items"][1]["sku"] == "CPU-AMD-7800X3D"   # $449.00
