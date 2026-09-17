"""
Unit Tests for Compatibility Engine Deterministic Rules (Module 14).
"""

from decimal import Decimal
import pytest

from app.modules.compatibility.rules import (
    check_cooler_case,
    check_cooler_cpu,
    check_cpu_motherboard,
    check_gpu_case,
    check_motherboard_case,
    check_psu_capacity,
    check_ram_motherboard,
    check_ram_speed,
    check_storage_motherboard,
)
from app.modules.compatibility.schemas import RuleIdentifier, RuleStatus
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


def _make_dummy_product(pid: int, name: str, sku: str) -> Product:
    return Product(
        id=pid,
        name=name,
        sku=sku,
        slug=sku.lower(),
        price=Decimal("100.00"),
        status=ProductStatus.ACTIVE.value,
        is_active=True,
    )


# =========================================================================
# 1. CPU <-> MOTHERBOARD SOCKET RULES
# =========================================================================

def test_cpu_motherboard_socket_match():
    cpu = _make_dummy_product(1, "Ryzen 7 7800X3D", "CPU-7800X3D")
    cpu.cpu_spec = CpuSpecification(socket="AM5", tdp_watts=120)
    mb = _make_dummy_product(2, "B650 Tomahawk", "MB-B650")
    mb.motherboard_spec = MotherboardSpecification(socket="AM5")

    res = check_cpu_motherboard(cpu, mb)
    assert res.rule == RuleIdentifier.CPU_SOCKET.value
    assert res.status == RuleStatus.PASS
    assert "matches" in res.message


def test_cpu_motherboard_socket_mismatch():
    cpu = _make_dummy_product(1, "Ryzen 7 7800X3D", "CPU-7800X3D")
    cpu.cpu_spec = CpuSpecification(socket="AM5", tdp_watts=120)
    mb = _make_dummy_product(2, "Z790 Gaming", "MB-Z790")
    mb.motherboard_spec = MotherboardSpecification(socket="LGA1700")

    res = check_cpu_motherboard(cpu, mb)
    assert res.rule == RuleIdentifier.CPU_SOCKET.value
    assert res.status == RuleStatus.FAIL
    assert "Incompatible socket" in res.message


def test_cpu_motherboard_socket_missing():
    cpu = _make_dummy_product(1, "Generic CPU", "CPU-GEN")
    cpu.cpu_spec = CpuSpecification(socket="", tdp_watts=65)
    mb = _make_dummy_product(2, "Generic MB", "MB-GEN")
    mb.motherboard_spec = None

    res = check_cpu_motherboard(cpu, mb)
    assert res.rule == RuleIdentifier.CPU_SOCKET.value
    assert res.status == RuleStatus.WARNING
    assert "could not be fully verified" in res.message


# =========================================================================
# 2. RAM <-> MOTHERBOARD MEMORY TYPE RULES
# =========================================================================

def test_ram_motherboard_type_match():
    ram = _make_dummy_product(3, "Corsair 32GB DDR5", "RAM-DDR5")
    ram.memory_spec = MemorySpecification(memory_type="DDR5", speed_mhz=6000)
    mb = _make_dummy_product(2, "B650 Tomahawk", "MB-B650")
    mb.motherboard_spec = MotherboardSpecification(memory_type="DDR5")

    res = check_ram_motherboard(ram, mb)
    assert res.rule == RuleIdentifier.RAM_TYPE.value
    assert res.status == RuleStatus.PASS
    assert "matches" in res.message


def test_ram_motherboard_type_mismatch():
    ram = _make_dummy_product(3, "Corsair 16GB DDR4", "RAM-DDR4")
    ram.memory_spec = MemorySpecification(memory_type="DDR4", speed_mhz=3200)
    mb = _make_dummy_product(2, "B650 Tomahawk", "MB-B650")
    mb.motherboard_spec = MotherboardSpecification(memory_type="DDR5")

    res = check_ram_motherboard(ram, mb)
    assert res.rule == RuleIdentifier.RAM_TYPE.value
    assert res.status == RuleStatus.FAIL
    assert "Incompatible memory type" in res.message


def test_ram_motherboard_type_missing():
    ram = _make_dummy_product(3, "Generic RAM", "RAM-GEN")
    ram.memory_spec = None
    mb = _make_dummy_product(2, "B650 Tomahawk", "MB-B650")
    mb.motherboard_spec = MotherboardSpecification(memory_type="DDR5")

    res = check_ram_motherboard(ram, mb)
    assert res.rule == RuleIdentifier.RAM_TYPE.value
    assert res.status == RuleStatus.WARNING


# =========================================================================
# 3. RAM SPEED <-> MOTHERBOARD RULES
# =========================================================================

def test_ram_speed_supported():
    ram = _make_dummy_product(3, "Corsair 32GB DDR5", "RAM-DDR5")
    ram.memory_spec = MemorySpecification(speed_mhz=6000)
    mb = _make_dummy_product(2, "B650 Tomahawk", "MB-B650")
    mb.motherboard_spec = MotherboardSpecification(max_memory_speed_mhz=6400)

    res = check_ram_speed(ram, mb)
    assert res.rule == RuleIdentifier.RAM_SPEED.value
    assert res.status == RuleStatus.PASS
    assert "supported" in res.message


def test_ram_speed_exceeded():
    ram = _make_dummy_product(3, "Corsair 32GB DDR5", "RAM-DDR5")
    ram.memory_spec = MemorySpecification(speed_mhz=7200)
    mb = _make_dummy_product(2, "B650 Tomahawk", "MB-B650")
    mb.motherboard_spec = MotherboardSpecification(max_memory_speed_mhz=6000)

    res = check_ram_speed(ram, mb)
    assert res.rule == RuleIdentifier.RAM_SPEED.value
    assert res.status == RuleStatus.FAIL
    assert "exceeds" in res.message


def test_ram_speed_motherboard_speed_unspecified():
    ram = _make_dummy_product(3, "Corsair 32GB DDR5", "RAM-DDR5")
    ram.memory_spec = MemorySpecification(speed_mhz=6000)
    mb = _make_dummy_product(2, "B650 Tomahawk", "MB-B650")
    mb.motherboard_spec = MotherboardSpecification(max_memory_speed_mhz=None)

    res = check_ram_speed(ram, mb)
    assert res.rule == RuleIdentifier.RAM_SPEED.value
    assert res.status == RuleStatus.WARNING
    assert "motherboard maximum memory speed is not specified" in res.message


# =========================================================================
# 4. GPU <-> CASE CLEARANCE RULES
# =========================================================================

def test_gpu_case_clearance_fits():
    gpu = _make_dummy_product(4, "RTX 4070", "GPU-4070")
    gpu.gpu_spec = GpuSpecification(length_mm=242)
    case = _make_dummy_product(5, "4000D Airflow", "CASE-4000D")
    case.case_spec = CaseSpecification(max_gpu_length_mm=360)

    res = check_gpu_case(gpu, case)
    assert res.rule == RuleIdentifier.GPU_CASE_CLEARANCE.value
    assert res.status == RuleStatus.PASS
    assert "fits" in res.message


def test_gpu_case_clearance_exceeded():
    gpu = _make_dummy_product(4, "RTX 4090 Strix", "GPU-4090")
    gpu.gpu_spec = GpuSpecification(length_mm=358)
    case = _make_dummy_product(5, "Mini-ITX Case", "CASE-MINI")
    case.case_spec = CaseSpecification(max_gpu_length_mm=320)

    res = check_gpu_case(gpu, case)
    assert res.rule == RuleIdentifier.GPU_CASE_CLEARANCE.value
    assert res.status == RuleStatus.FAIL
    assert "exceeds" in res.message


def test_gpu_case_clearance_missing():
    gpu = _make_dummy_product(4, "RTX 4070", "GPU-4070")
    gpu.gpu_spec = None
    case = _make_dummy_product(5, "4000D Airflow", "CASE-4000D")
    case.case_spec = CaseSpecification(max_gpu_length_mm=360)

    res = check_gpu_case(gpu, case)
    assert res.rule == RuleIdentifier.GPU_CASE_CLEARANCE.value
    assert res.status == RuleStatus.WARNING


# =========================================================================
# 5. MOTHERBOARD <-> CASE FORM FACTOR RULES
# =========================================================================

def test_motherboard_case_form_factor_supported():
    mb = _make_dummy_product(2, "B650 Tomahawk", "MB-B650")
    mb.motherboard_spec = MotherboardSpecification(form_factor="ATX")
    case = _make_dummy_product(5, "4000D Airflow", "CASE-4000D")
    case.case_spec = CaseSpecification(supported_motherboard_form_factors=["ATX", "Micro-ATX", "Mini-ITX"])

    res = check_motherboard_case(mb, case)
    assert res.rule == RuleIdentifier.MOTHERBOARD_FORM_FACTOR.value
    assert res.status == RuleStatus.PASS
    assert "supported" in res.message


def test_motherboard_case_form_factor_unsupported():
    mb = _make_dummy_product(2, "ATX Board", "MB-ATX")
    mb.motherboard_spec = MotherboardSpecification(form_factor="ATX")
    case = _make_dummy_product(5, "Small ITX Case", "CASE-ITX")
    case.case_spec = CaseSpecification(supported_motherboard_form_factors=["Mini-ITX"])

    res = check_motherboard_case(mb, case)
    assert res.rule == RuleIdentifier.MOTHERBOARD_FORM_FACTOR.value
    assert res.status == RuleStatus.FAIL
    assert "not supported" in res.message


def test_motherboard_case_form_factor_missing():
    mb = _make_dummy_product(2, "Board", "MB-GEN")
    mb.motherboard_spec = MotherboardSpecification(form_factor="ATX")
    case = _make_dummy_product(5, "Case", "CASE-GEN")
    case.case_spec = CaseSpecification(supported_motherboard_form_factors=[])

    res = check_motherboard_case(mb, case)
    assert res.rule == RuleIdentifier.MOTHERBOARD_FORM_FACTOR.value
    assert res.status == RuleStatus.WARNING


# =========================================================================
# 6. STORAGE <-> MOTHERBOARD INTERFACE RULES
# =========================================================================

def test_storage_motherboard_interface_supported():
    storage = _make_dummy_product(6, "Samsung 990 Pro", "SSD-990")
    storage.storage_spec = StorageSpecification(interface="PCIe 4.0 NVMe", form_factor="M.2 2280")
    mb = _make_dummy_product(2, "B650 Tomahawk", "MB-B650")
    mb.motherboard_spec = MotherboardSpecification(
        supported_storage_interfaces=["PCIe 4.0 NVMe", "SATA III", "M.2 NVMe"]
    )

    res = check_storage_motherboard(storage, mb)
    assert res.rule == RuleIdentifier.STORAGE_INTERFACE.value
    assert res.status == RuleStatus.PASS


def test_storage_motherboard_interface_unsupported():
    storage = _make_dummy_product(6, "Enterprise SAS SSD", "SSD-SAS")
    storage.storage_spec = StorageSpecification(interface="SAS-3", form_factor="2.5 inch")
    mb = _make_dummy_product(2, "Consumer B650", "MB-B650")
    mb.motherboard_spec = MotherboardSpecification(
        supported_storage_interfaces=["M.2 NVMe", "SATA III"]
    )

    res = check_storage_motherboard(storage, mb)
    assert res.rule == RuleIdentifier.STORAGE_INTERFACE.value
    assert res.status == RuleStatus.FAIL


def test_storage_motherboard_interface_unspecified():
    storage = _make_dummy_product(6, "Samsung 990 Pro", "SSD-990")
    storage.storage_spec = StorageSpecification(interface="PCIe 4.0 NVMe", form_factor="M.2 2280")
    mb = _make_dummy_product(2, "B650 Tomahawk", "MB-B650")
    mb.motherboard_spec = MotherboardSpecification(supported_storage_interfaces=None)

    res = check_storage_motherboard(storage, mb)
    assert res.rule == RuleIdentifier.STORAGE_INTERFACE.value
    assert res.status == RuleStatus.WARNING
    assert "motherboard supported storage interfaces are not specified" in res.message


# =========================================================================
# 7. PSU CAPACITY DETERMINISTIC CALCULATION RULES
# =========================================================================

def test_psu_capacity_sufficient():
    # CPU: 120W, GPU: 220W, Base: 75W -> total = 415W
    # required = ceil(415 * 1.25) = 519W
    # PSU: 750W -> PASS
    cpu = _make_dummy_product(1, "Ryzen 7 7800X3D", "CPU-7800X3D")
    cpu.cpu_spec = CpuSpecification(tdp_watts=120)
    gpu = _make_dummy_product(4, "RTX 4070", "GPU-4070")
    gpu.gpu_spec = GpuSpecification(tdp_watts=220)
    psu = _make_dummy_product(7, "Corsair RM750", "PSU-750")
    psu.psu_spec = PsuSpecification(wattage=750)

    res, est_power, req_psu = check_psu_capacity(psu, cpu, gpu)
    assert res.rule == RuleIdentifier.PSU_CAPACITY.value
    assert res.status == RuleStatus.PASS
    assert est_power == 415
    assert req_psu == 519
    assert "sufficient" in res.message or "meets" in res.message


def test_psu_capacity_insufficient():
    # CPU: 120W, GPU: 220W, Base: 75W -> required = 519W
    # PSU: 450W -> FAIL
    cpu = _make_dummy_product(1, "Ryzen 7 7800X3D", "CPU-7800X3D")
    cpu.cpu_spec = CpuSpecification(tdp_watts=120)
    gpu = _make_dummy_product(4, "RTX 4070", "GPU-4070")
    gpu.gpu_spec = GpuSpecification(tdp_watts=220)
    psu = _make_dummy_product(7, "Budget 450W", "PSU-450")
    psu.psu_spec = PsuSpecification(wattage=450)

    res, est_power, req_psu = check_psu_capacity(psu, cpu, gpu)
    assert res.rule == RuleIdentifier.PSU_CAPACITY.value
    assert res.status == RuleStatus.FAIL
    assert est_power == 415
    assert req_psu == 519
    assert "Insufficient PSU capacity" in res.message


def test_psu_capacity_missing_cpu_tdp():
    cpu = _make_dummy_product(1, "Ryzen 7 7800X3D", "CPU-7800X3D")
    cpu.cpu_spec = CpuSpecification(tdp_watts=None)
    psu = _make_dummy_product(7, "Corsair RM750", "PSU-750")
    psu.psu_spec = PsuSpecification(wattage=750)

    res, est_power, req_psu = check_psu_capacity(psu, cpu, None)
    assert res.rule == RuleIdentifier.PSU_CAPACITY.value
    assert res.status == RuleStatus.WARNING
    assert "CPU power specification (TDP) is missing" in res.message


# =========================================================================
# 8. COOLER COMPATIBILITY RULES
# =========================================================================

def test_cooler_cpu_socket_supported():
    cpu = _make_dummy_product(1, "Ryzen 7 7800X3D", "CPU-7800X3D")
    cpu.cpu_spec = CpuSpecification(socket="AM5")
    cooler = _make_dummy_product(8, "DeepCool AK620", "COOLER-AK620")
    cooler.cooling_spec = CoolingSpecification(supported_sockets=["AM4", "AM5", "LGA1700"], height_mm=160)

    res = check_cooler_cpu(cooler, cpu)
    assert res.rule == RuleIdentifier.COOLER_SOCKET.value
    assert res.status == RuleStatus.PASS


def test_cooler_cpu_socket_unsupported():
    cpu = _make_dummy_product(1, "Intel i9 14900K", "CPU-14900K")
    cpu.cpu_spec = CpuSpecification(socket="LGA1700")
    cooler = _make_dummy_product(8, "Old AMD Cooler", "COOLER-AMD")
    cooler.cooling_spec = CoolingSpecification(supported_sockets=["AM4", "AM3"], height_mm=120)

    res = check_cooler_cpu(cooler, cpu)
    assert res.rule == RuleIdentifier.COOLER_SOCKET.value
    assert res.status == RuleStatus.FAIL


def test_cooler_case_height_clearance():
    cooler = _make_dummy_product(8, "DeepCool AK620", "COOLER-AK620")
    cooler.cooling_spec = CoolingSpecification(height_mm=160)
    case = _make_dummy_product(5, "Corsair 4000D", "CASE-4000D")
    case.case_spec = CaseSpecification(max_cpu_cooler_height_mm=170)

    res = check_cooler_case(cooler, case)
    assert res.rule == RuleIdentifier.COOLER_CASE_HEIGHT.value
    assert res.status == RuleStatus.PASS


def test_cooler_case_height_exceeded():
    cooler = _make_dummy_product(8, "Giant Air Cooler", "COOLER-GIANT")
    cooler.cooling_spec = CoolingSpecification(height_mm=180)
    case = _make_dummy_product(5, "Slim Case", "CASE-SLIM")
    case.case_spec = CaseSpecification(max_cpu_cooler_height_mm=150)

    res = check_cooler_case(cooler, case)
    assert res.rule == RuleIdentifier.COOLER_CASE_HEIGHT.value
    assert res.status == RuleStatus.FAIL
