"""
Service Tests for CompatibilityService (Module 14).
"""

from decimal import Decimal
import pytest
from app.core.exceptions import HTTPException

from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.compatibility.schemas import (
    CompatibilityCheckRequest,
    RuleStatus,
)
from app.modules.compatibility.service import CompatibilityService
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
def hardware_catalog(db_session):
    """Creates a full set of hardware components with authoritative specifications."""
    cat_cpu = Category(name="Processors", slug="cpu", is_active=True)
    cat_mb = Category(name="Motherboards", slug="motherboard", is_active=True)
    cat_ram = Category(name="Memory", slug="memory", is_active=True)
    cat_gpu = Category(name="Graphics Cards", slug="gpu", is_active=True)
    cat_psu = Category(name="Power Supplies", slug="psu", is_active=True)
    cat_case = Category(name="Cases", slug="case", is_active=True)
    cat_storage = Category(name="Storage", slug="storage", is_active=True)
    brand = Brand(name="BuildTech Parts", slug="buildtech-parts", is_active=True)

    db_session.add_all([cat_cpu, cat_mb, cat_ram, cat_gpu, cat_psu, cat_case, cat_storage, brand])
    db_session.commit()

    # 1. Compatible CPU (AM5, 120W)
    cpu_am5 = Product(
        sku="CPU-AM5-7800X3D",
        name="AMD Ryzen 7 7800X3D",
        slug="amd-ryzen-7-7800x3d",
        category_id=cat_cpu.id,
        brand_id=brand.id,
        price=Decimal("449.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 2. Incompatible CPU (LGA1700, 150W)
    cpu_intel = Product(
        sku="CPU-INTEL-14700K",
        name="Intel Core i7-14700K",
        slug="intel-core-i7-14700k",
        category_id=cat_cpu.id,
        brand_id=brand.id,
        price=Decimal("409.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 3. Compatible AM5 Motherboard (ATX, DDR5, max 6400MHz, NVMe support)
    mb_am5 = Product(
        sku="MB-AM5-B650",
        name="MSI B650 Tomahawk WiFi",
        slug="msi-b650-tomahawk-wifi",
        category_id=cat_mb.id,
        brand_id=brand.id,
        price=Decimal("219.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 4. AM5 Motherboard with incomplete specs (no max RAM speed, no storage interface list)
    mb_incomplete = Product(
        sku="MB-INCOMPLETE",
        name="Basic AM5 Board",
        slug="basic-am5-board",
        category_id=cat_mb.id,
        brand_id=brand.id,
        price=Decimal("150.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 5. Compatible RAM (DDR5, 6000MHz)
    ram_ddr5 = Product(
        sku="RAM-32GB-DDR5",
        name="Corsair Vengeance 32GB DDR5 6000",
        slug="corsair-vengeance-32gb-ddr5-6000",
        category_id=cat_ram.id,
        brand_id=brand.id,
        price=Decimal("119.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 6. Incompatible RAM (DDR4, 3200MHz)
    ram_ddr4 = Product(
        sku="RAM-16GB-DDR4",
        name="Corsair Vengeance 16GB DDR4 3200",
        slug="corsair-vengeance-16gb-ddr4-3200",
        category_id=cat_ram.id,
        brand_id=brand.id,
        price=Decimal("59.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 7. GPU (242mm length, 220W TDP)
    gpu_normal = Product(
        sku="GPU-RTX-4070",
        name="NVIDIA RTX 4070 Super",
        slug="nvidia-rtx-4070-super",
        category_id=cat_gpu.id,
        brand_id=brand.id,
        price=Decimal("599.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 8. Large GPU (360mm length, 350W TDP)
    gpu_large = Product(
        sku="GPU-RTX-4090",
        name="ASUS ROG Strix RTX 4090",
        slug="asus-rog-strix-rtx-4090",
        category_id=cat_gpu.id,
        brand_id=brand.id,
        price=Decimal("1799.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 9. Case with 340mm GPU clearance, ATX support
    case_mid = Product(
        sku="CASE-MID-TOWER",
        name="Corsair 4000D Airflow",
        slug="corsair-4000d-airflow",
        category_id=cat_case.id,
        brand_id=brand.id,
        price=Decimal("104.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 10. Sufficient PSU (850W)
    psu_850 = Product(
        sku="PSU-850W",
        name="Corsair RM850x",
        slug="corsair-rm850x",
        category_id=cat_psu.id,
        brand_id=brand.id,
        price=Decimal("139.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 11. Insufficient PSU (400W)
    psu_400 = Product(
        sku="PSU-400W",
        name="Basic 400W PSU",
        slug="basic-400w-psu",
        category_id=cat_psu.id,
        brand_id=brand.id,
        price=Decimal("49.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )
    # 12. Storage (M.2 NVMe)
    ssd_nvme = Product(
        sku="SSD-2TB-NVME",
        name="Samsung 990 Pro 2TB",
        slug="samsung-990-pro-2tb",
        category_id=cat_storage.id,
        brand_id=brand.id,
        price=Decimal("179.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )

    db_session.add_all([
        cpu_am5, cpu_intel, mb_am5, mb_incomplete,
        ram_ddr5, ram_ddr4, gpu_normal, gpu_large,
        case_mid, psu_850, psu_400, ssd_nvme
    ])
    db_session.commit()

    # Specifications
    cpu_am5_spec = CpuSpecification(
        product_id=cpu_am5.id,
        socket="AM5",
        core_count=8,
        thread_count=16,
        base_clock_ghz=Decimal("4.20"),
        boost_clock_ghz=Decimal("5.00"),
        tdp_watts=120,
    )
    cpu_intel_spec = CpuSpecification(
        product_id=cpu_intel.id,
        socket="LGA1700",
        core_count=20,
        thread_count=28,
        base_clock_ghz=Decimal("3.40"),
        boost_clock_ghz=Decimal("5.60"),
        tdp_watts=150,
    )
    mb_am5_spec = MotherboardSpecification(
        product_id=mb_am5.id,
        socket="AM5",
        chipset="B650",
        form_factor="ATX",
        memory_type="DDR5",
        memory_slots=4,
        max_memory_gb=192,
        wifi=True,
        max_memory_speed_mhz=6400,
        supported_storage_interfaces=["PCIe 4.0 NVMe", "SATA III", "M.2 NVMe"],
    )
    mb_incomplete_spec = MotherboardSpecification(
        product_id=mb_incomplete.id,
        socket="AM5",
        chipset="A620",
        form_factor="ATX",
        memory_type="DDR5",
        memory_slots=2,
        max_memory_gb=64,
        wifi=False,
        max_memory_speed_mhz=None,
        supported_storage_interfaces=None,
    )
    ram_ddr5_spec = MemorySpecification(
        product_id=ram_ddr5.id,
        memory_type="DDR5",
        capacity_gb=32,
        speed_mhz=6000,
        module_count=2,
    )
    ram_ddr4_spec = MemorySpecification(
        product_id=ram_ddr4.id,
        memory_type="DDR4",
        capacity_gb=16,
        speed_mhz=3200,
        module_count=2,
    )
    gpu_normal_spec = GpuSpecification(
        product_id=gpu_normal.id,
        chipset="AD104",
        vram_gb=12,
        memory_type="GDDR6X",
        boost_clock_mhz=2475,
        length_mm=242,
        tdp_watts=220,
        recommended_psu_watts=650,
    )
    gpu_large_spec = GpuSpecification(
        product_id=gpu_large.id,
        chipset="AD102",
        vram_gb=24,
        memory_type="GDDR6X",
        boost_clock_mhz=2520,
        length_mm=360,
        tdp_watts=350,
        recommended_psu_watts=850,
    )
    case_mid_spec = CaseSpecification(
        product_id=case_mid.id,
        case_type="Mid Tower",
        supported_motherboard_form_factors=["ATX", "Micro-ATX", "Mini-ITX"],
        max_gpu_length_mm=340,
        max_cpu_cooler_height_mm=170,
        psu_form_factor="ATX",
    )
    psu_850_spec = PsuSpecification(
        product_id=psu_850.id,
        wattage=850,
        efficiency_rating="80+ Gold",
        modularity="Full",
        form_factor="ATX",
    )
    psu_400_spec = PsuSpecification(
        product_id=psu_400.id,
        wattage=400,
        efficiency_rating="80+ Bronze",
        modularity="Non-Modular",
        form_factor="ATX",
    )
    ssd_nvme_spec = StorageSpecification(
        product_id=ssd_nvme.id,
        storage_type="SSD",
        capacity_gb=2000,
        interface="PCIe 4.0 NVMe",
        form_factor="M.2 2280",
    )

    db_session.add_all([
        cpu_am5_spec, cpu_intel_spec, mb_am5_spec, mb_incomplete_spec,
        ram_ddr5_spec, ram_ddr4_spec, gpu_normal_spec, gpu_large_spec,
        case_mid_spec, psu_850_spec, psu_400_spec, ssd_nvme_spec
    ])
    db_session.commit()

    return {
        "cpu_am5": cpu_am5,
        "cpu_intel": cpu_intel,
        "mb_am5": mb_am5,
        "mb_incomplete": mb_incomplete,
        "ram_ddr5": ram_ddr5,
        "ram_ddr4": ram_ddr4,
        "gpu_normal": gpu_normal,
        "gpu_large": gpu_large,
        "case_mid": case_mid,
        "psu_850": psu_850,
        "psu_400": psu_400,
        "ssd_nvme": ssd_nvme,
    }


def test_service_all_components_pass(db_session, hardware_catalog):
    """Test full system build where all components are mutually compatible."""
    c = hardware_catalog
    service = CompatibilityService(db_session)

    product_ids = [
        c["cpu_am5"].id,
        c["mb_am5"].id,
        c["ram_ddr5"].id,
        c["gpu_normal"].id,
        c["case_mid"].id,
        c["psu_850"].id,
        c["ssd_nvme"].id,
    ]

    req = CompatibilityCheckRequest(product_ids=product_ids)
    res = service.check_compatibility(req)

    assert res.status == RuleStatus.PASS
    assert res.fail_count == 0
    assert res.warning_count == 0
    assert res.pass_count > 0
    assert "All selected components are compatible" in res.summary
    assert res.estimated_system_power_watts == 415  # 120 + 220 + 75
    assert res.required_psu_watts == 519  # ceil(415 * 1.25)


def test_service_one_failure_among_passes(db_session, hardware_catalog):
    """Test when GPU is too long for the case, overall status must be FAIL."""
    c = hardware_catalog
    service = CompatibilityService(db_session)

    # gpu_large length = 360mm > case_mid max = 340mm
    product_ids = [
        c["cpu_am5"].id,
        c["mb_am5"].id,
        c["ram_ddr5"].id,
        c["gpu_large"].id,
        c["case_mid"].id,
        c["psu_850"].id,
    ]

    req = CompatibilityCheckRequest(product_ids=product_ids)
    res = service.check_compatibility(req)

    assert res.status == RuleStatus.FAIL
    assert res.fail_count >= 1
    assert any(check.rule == "GPU_CASE_CLEARANCE" and check.status == RuleStatus.FAIL for check in res.checks)


def test_service_warning_plus_pass(db_session, hardware_catalog):
    """Test that missing motherboard spec fields produce WARNING, never converted to PASS."""
    c = hardware_catalog
    service = CompatibilityService(db_session)

    # mb_incomplete lacks max_memory_speed and supported_storage_interfaces
    product_ids = [
        c["cpu_am5"].id,
        c["mb_incomplete"].id,
        c["ram_ddr5"].id,
    ]

    req = CompatibilityCheckRequest(product_ids=product_ids)
    res = service.check_compatibility(req)

    assert res.status == RuleStatus.WARNING
    assert res.fail_count == 0
    assert res.warning_count >= 1
    # RAM_SPEED should be WARNING
    ram_speed_check = next(ch for ch in res.checks if ch.rule == "RAM_SPEED")
    assert ram_speed_check.status == RuleStatus.WARNING


def test_service_multiple_failures(db_session, hardware_catalog):
    """Test multiple failures (socket mismatch + RAM type mismatch + insufficient PSU)."""
    c = hardware_catalog
    service = CompatibilityService(db_session)

    product_ids = [
        c["cpu_intel"].id,  # LGA1700
        c["mb_am5"].id,     # AM5
        c["ram_ddr4"].id,   # DDR4 (mb is DDR5)
        c["psu_400"].id,    # 400W (needs 519W+)
        c["gpu_normal"].id,
    ]

    req = CompatibilityCheckRequest(product_ids=product_ids)
    res = service.check_compatibility(req)

    assert res.status == RuleStatus.FAIL
    assert res.fail_count >= 3
    failed_rules = {ch.rule for ch in res.checks if ch.status == RuleStatus.FAIL}
    assert "CPU_SOCKET" in failed_rules
    assert "RAM_TYPE" in failed_rules
    assert "PSU_CAPACITY" in failed_rules


def test_service_missing_product_raises_404(db_session, hardware_catalog):
    """Test that passing nonexistent product IDs raises 404."""
    service = CompatibilityService(db_session)
    req = CompatibilityCheckRequest(product_ids=[99999, 99998])

    with pytest.raises(HTTPException) as exc_info:
        service.check_compatibility(req)

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


def test_service_determinism(db_session, hardware_catalog):
    """Verify that the identical input produces strictly identical results across 5 consecutive runs."""
    c = hardware_catalog
    service = CompatibilityService(db_session)

    product_ids = [
        c["cpu_am5"].id,
        c["mb_am5"].id,
        c["ram_ddr5"].id,
        c["gpu_normal"].id,
        c["case_mid"].id,
        c["psu_850"].id,
    ]
    req = CompatibilityCheckRequest(product_ids=product_ids)

    first_run = service.check_compatibility(req)

    for _ in range(4):
        run = service.check_compatibility(req)
        assert run.status == first_run.status
        assert run.summary == first_run.summary
        assert run.pass_count == first_run.pass_count
        assert run.warning_count == first_run.warning_count
        assert run.fail_count == first_run.fail_count
        assert run.estimated_system_power_watts == first_run.estimated_system_power_watts
        assert run.required_psu_watts == first_run.required_psu_watts
        assert len(run.checks) == len(first_run.checks)
        for c1, c2 in zip(first_run.checks, run.checks):
            assert c1.rule == c2.rule
            assert c1.status == c2.status
            assert c1.message == c2.message
