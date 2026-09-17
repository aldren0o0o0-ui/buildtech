"""
Deterministic Hardware Compatibility Rules (Module 14).

Pure, isolated, deterministic rule functions operating exclusively
on authoritative product specifications loaded from PostgreSQL.
"""

import math
import re
from typing import List, Optional, Tuple

from app.modules.compatibility.schemas import (
    RuleCheckResult,
    RuleIdentifier,
    RuleStatus,
)
from app.modules.products.models import Product

# Engineering constants for deterministic power calculations
BASE_SYSTEM_ALLOWANCE_WATTS = 75  # Motherboard, RAM, storage, chipset, cooling fans
SAFETY_MARGIN_MULTIPLIER = 1.25   # 25% standard engineering safety margin


def _normalize_string(val: Optional[str]) -> str:
    """Normalize a string by stripping and converting to uppercase."""
    if not val:
        return ""
    return re.sub(r"[\s\-_]+", "", str(val).strip().upper())


def check_cpu_motherboard(
    cpu_product: Product,
    motherboard_product: Product,
) -> RuleCheckResult:
    """
    Evaluates socket compatibility between CPU and Motherboard.
    Rule: CPU.socket == Motherboard.socket
    """
    comp_ids = [cpu_product.id, motherboard_product.id]
    cpu_spec = getattr(cpu_product, "cpu_spec", None)
    mb_spec = getattr(motherboard_product, "motherboard_spec", None)

    if not cpu_spec or not cpu_spec.socket or not mb_spec or not mb_spec.socket:
        return RuleCheckResult(
            rule=RuleIdentifier.CPU_SOCKET.value,
            status=RuleStatus.WARNING,
            message="Compatibility could not be fully verified because CPU or motherboard socket specification is missing.",
            component_ids=comp_ids,
            actual=getattr(cpu_spec, "socket", None),
            expected=getattr(mb_spec, "socket", None),
        )

    norm_cpu = _normalize_string(cpu_spec.socket)
    norm_mb = _normalize_string(mb_spec.socket)

    if norm_cpu == norm_mb:
        return RuleCheckResult(
            rule=RuleIdentifier.CPU_SOCKET.value,
            status=RuleStatus.PASS,
            message=f"CPU socket ({cpu_spec.socket}) matches motherboard socket ({mb_spec.socket}).",
            component_ids=comp_ids,
            actual=cpu_spec.socket,
            expected=mb_spec.socket,
        )
    else:
        return RuleCheckResult(
            rule=RuleIdentifier.CPU_SOCKET.value,
            status=RuleStatus.FAIL,
            message=f"Incompatible socket: CPU requires socket '{cpu_spec.socket}', but motherboard provides '{mb_spec.socket}'.",
            component_ids=comp_ids,
            actual=cpu_spec.socket,
            expected=mb_spec.socket,
        )


def check_ram_motherboard(
    ram_product: Product,
    motherboard_product: Product,
) -> RuleCheckResult:
    """
    Evaluates memory technology compatibility between RAM and Motherboard.
    Rule: RAM.memory_type == Motherboard.memory_type (e.g. DDR4 == DDR4, DDR5 == DDR5)
    """
    comp_ids = [ram_product.id, motherboard_product.id]
    ram_spec = getattr(ram_product, "memory_spec", None)
    mb_spec = getattr(motherboard_product, "motherboard_spec", None)

    if not ram_spec or not ram_spec.memory_type or not mb_spec or not mb_spec.memory_type:
        return RuleCheckResult(
            rule=RuleIdentifier.RAM_TYPE.value,
            status=RuleStatus.WARNING,
            message="Compatibility could not be fully verified because RAM or motherboard memory type specification is missing.",
            component_ids=comp_ids,
            actual=getattr(ram_spec, "memory_type", None),
            expected=getattr(mb_spec, "memory_type", None),
        )

    norm_ram = _normalize_string(ram_spec.memory_type)
    norm_mb = _normalize_string(mb_spec.memory_type)

    if norm_ram == norm_mb:
        return RuleCheckResult(
            rule=RuleIdentifier.RAM_TYPE.value,
            status=RuleStatus.PASS,
            message=f"RAM memory type ({ram_spec.memory_type}) matches motherboard memory type ({mb_spec.memory_type}).",
            component_ids=comp_ids,
            actual=ram_spec.memory_type,
            expected=mb_spec.memory_type,
        )
    else:
        return RuleCheckResult(
            rule=RuleIdentifier.RAM_TYPE.value,
            status=RuleStatus.FAIL,
            message=f"Incompatible memory type: RAM is {ram_spec.memory_type}, but motherboard requires {mb_spec.memory_type}.",
            component_ids=comp_ids,
            actual=ram_spec.memory_type,
            expected=mb_spec.memory_type,
        )


def check_ram_speed(
    ram_product: Product,
    motherboard_product: Product,
) -> RuleCheckResult:
    """
    Evaluates RAM speed against Motherboard maximum supported memory speed.
    Rule: RAM.speed_mhz <= Motherboard.max_memory_speed_mhz
    """
    comp_ids = [ram_product.id, motherboard_product.id]
    ram_spec = getattr(ram_product, "memory_spec", None)
    mb_spec = getattr(motherboard_product, "motherboard_spec", None)

    if not ram_spec or not ram_spec.speed_mhz:
        return RuleCheckResult(
            rule=RuleIdentifier.RAM_SPEED.value,
            status=RuleStatus.WARNING,
            message="Compatibility could not be fully verified because RAM speed specification is missing.",
            component_ids=comp_ids,
        )

    if not mb_spec or getattr(mb_spec, "max_memory_speed_mhz", None) is None:
        return RuleCheckResult(
            rule=RuleIdentifier.RAM_SPEED.value,
            status=RuleStatus.WARNING,
            message="Compatibility could not be fully verified because motherboard maximum memory speed is not specified.",
            component_ids=comp_ids,
            actual=f"{ram_spec.speed_mhz} MHz",
            expected="Unspecified",
        )

    max_speed = mb_spec.max_memory_speed_mhz
    if ram_spec.speed_mhz <= max_speed:
        return RuleCheckResult(
            rule=RuleIdentifier.RAM_SPEED.value,
            status=RuleStatus.PASS,
            message=f"RAM speed ({ram_spec.speed_mhz} MHz) is supported within motherboard maximum speed ({max_speed} MHz).",
            component_ids=comp_ids,
            actual=f"{ram_spec.speed_mhz} MHz",
            expected=f"<= {max_speed} MHz",
        )
    else:
        return RuleCheckResult(
            rule=RuleIdentifier.RAM_SPEED.value,
            status=RuleStatus.FAIL,
            message=f"RAM speed ({ram_spec.speed_mhz} MHz) exceeds motherboard maximum supported speed ({max_speed} MHz).",
            component_ids=comp_ids,
            actual=f"{ram_spec.speed_mhz} MHz",
            expected=f"<= {max_speed} MHz",
        )


def check_gpu_case(
    gpu_product: Product,
    case_product: Product,
) -> RuleCheckResult:
    """
    Evaluates physical GPU clearance inside the selected Case.
    Rule: GPU.length_mm <= Case.max_gpu_length_mm
    """
    comp_ids = [gpu_product.id, case_product.id]
    gpu_spec = getattr(gpu_product, "gpu_spec", None)
    case_spec = getattr(case_product, "case_spec", None)

    if not gpu_spec or not gpu_spec.length_mm or not case_spec or not case_spec.max_gpu_length_mm:
        return RuleCheckResult(
            rule=RuleIdentifier.GPU_CASE_CLEARANCE.value,
            status=RuleStatus.WARNING,
            message="Compatibility could not be fully verified because GPU length or case clearance specification is missing.",
            component_ids=comp_ids,
            actual=getattr(gpu_spec, "length_mm", None),
            expected=getattr(case_spec, "max_gpu_length_mm", None),
        )

    if gpu_spec.length_mm <= case_spec.max_gpu_length_mm:
        return RuleCheckResult(
            rule=RuleIdentifier.GPU_CASE_CLEARANCE.value,
            status=RuleStatus.PASS,
            message=f"GPU length ({gpu_spec.length_mm} mm) fits within case maximum clearance ({case_spec.max_gpu_length_mm} mm).",
            component_ids=comp_ids,
            actual=f"{gpu_spec.length_mm} mm",
            expected=f"<= {case_spec.max_gpu_length_mm} mm",
        )
    else:
        return RuleCheckResult(
            rule=RuleIdentifier.GPU_CASE_CLEARANCE.value,
            status=RuleStatus.FAIL,
            message=f"GPU length ({gpu_spec.length_mm} mm) exceeds case maximum clearance ({case_spec.max_gpu_length_mm} mm).",
            component_ids=comp_ids,
            actual=f"{gpu_spec.length_mm} mm",
            expected=f"<= {case_spec.max_gpu_length_mm} mm",
        )


def check_motherboard_case(
    motherboard_product: Product,
    case_product: Product,
) -> RuleCheckResult:
    """
    Evaluates physical form factor compatibility between Motherboard and Case.
    Rule: Motherboard.form_factor in Case.supported_motherboard_form_factors
    """
    comp_ids = [motherboard_product.id, case_product.id]
    mb_spec = getattr(motherboard_product, "motherboard_spec", None)
    case_spec = getattr(case_product, "case_spec", None)

    if not mb_spec or not mb_spec.form_factor or not case_spec or not case_spec.supported_motherboard_form_factors:
        return RuleCheckResult(
            rule=RuleIdentifier.MOTHERBOARD_FORM_FACTOR.value,
            status=RuleStatus.WARNING,
            message="Compatibility could not be fully verified because motherboard form factor or case supported form factors specification is missing.",
            component_ids=comp_ids,
            actual=getattr(mb_spec, "form_factor", None),
            expected=getattr(case_spec, "supported_motherboard_form_factors", None),
        )

    norm_mb_ff = _normalize_string(mb_spec.form_factor)
    raw_supported = case_spec.supported_motherboard_form_factors
    if isinstance(raw_supported, list):
        norm_supported = [_normalize_string(x) for x in raw_supported]
    else:
        norm_supported = [_normalize_string(str(raw_supported))]

    if norm_mb_ff in norm_supported:
        return RuleCheckResult(
            rule=RuleIdentifier.MOTHERBOARD_FORM_FACTOR.value,
            status=RuleStatus.PASS,
            message=f"Motherboard form factor ({mb_spec.form_factor}) is supported by case.",
            component_ids=comp_ids,
            actual=mb_spec.form_factor,
            expected=raw_supported,
        )
    else:
        supported_str = ", ".join(raw_supported) if isinstance(raw_supported, list) else str(raw_supported)
        return RuleCheckResult(
            rule=RuleIdentifier.MOTHERBOARD_FORM_FACTOR.value,
            status=RuleStatus.FAIL,
            message=f"Motherboard form factor '{mb_spec.form_factor}' is not supported by case (supported: {supported_str}).",
            component_ids=comp_ids,
            actual=mb_spec.form_factor,
            expected=raw_supported,
        )


def check_storage_motherboard(
    storage_product: Product,
    motherboard_product: Product,
) -> RuleCheckResult:
    """
    Evaluates storage interface compatibility between Storage drive and Motherboard.
    Rule: Storage.interface in Motherboard.supported_storage_interfaces
    """
    comp_ids = [storage_product.id, motherboard_product.id]
    storage_spec = getattr(storage_product, "storage_spec", None)
    mb_spec = getattr(motherboard_product, "motherboard_spec", None)

    if not storage_spec or not storage_spec.interface:
        return RuleCheckResult(
            rule=RuleIdentifier.STORAGE_INTERFACE.value,
            status=RuleStatus.WARNING,
            message="Compatibility could not be fully verified because storage drive interface specification is missing.",
            component_ids=comp_ids,
        )

    supported_interfaces = getattr(mb_spec, "supported_storage_interfaces", None)
    if not mb_spec or supported_interfaces is None:
        return RuleCheckResult(
            rule=RuleIdentifier.STORAGE_INTERFACE.value,
            status=RuleStatus.WARNING,
            message="Compatibility could not be fully verified because motherboard supported storage interfaces are not specified.",
            component_ids=comp_ids,
            actual=f"{storage_spec.interface} ({storage_spec.form_factor})",
            expected="Unspecified",
        )

    norm_st_iface = _normalize_string(storage_spec.interface)
    norm_st_ff = _normalize_string(storage_spec.form_factor)
    norm_supported = [_normalize_string(x) for x in supported_interfaces] if isinstance(supported_interfaces, list) else [_normalize_string(str(supported_interfaces))]

    # Direct match or substring match (e.g. NVME in PCIE40NVME or SATA in SATAIII)
    is_supported = (
        norm_st_iface in norm_supported
        or norm_st_ff in norm_supported
        or any(norm_st_iface in s or s in norm_st_iface for s in norm_supported)
    )

    if is_supported:
        return RuleCheckResult(
            rule=RuleIdentifier.STORAGE_INTERFACE.value,
            status=RuleStatus.PASS,
            message=f"Storage interface ({storage_spec.interface}, {storage_spec.form_factor}) is supported by motherboard.",
            component_ids=comp_ids,
            actual=storage_spec.interface,
            expected=supported_interfaces,
        )
    else:
        supported_str = ", ".join(supported_interfaces) if isinstance(supported_interfaces, list) else str(supported_interfaces)
        return RuleCheckResult(
            rule=RuleIdentifier.STORAGE_INTERFACE.value,
            status=RuleStatus.FAIL,
            message=f"Storage interface '{storage_spec.interface}' is not supported by motherboard (supported: {supported_str}).",
            component_ids=comp_ids,
            actual=storage_spec.interface,
            expected=supported_interfaces,
        )


def check_psu_capacity(
    psu_product: Product,
    cpu_product: Optional[Product] = None,
    gpu_product: Optional[Product] = None,
) -> Tuple[RuleCheckResult, Optional[int], Optional[int]]:
    """
    Evaluates PSU wattage against calculated system power requirements.
    Deterministic formula:
        estimated_system_power = CPU_TDP + GPU_TDP + BASE_SYSTEM_ALLOWANCE_WATTS
        required_psu_wattage = ceil(estimated_system_power * SAFETY_MARGIN_MULTIPLIER)
    Returns: (RuleCheckResult, estimated_system_power, required_psu_wattage)
    """
    comp_ids = [psu_product.id]
    if cpu_product:
        comp_ids.append(cpu_product.id)
    if gpu_product:
        comp_ids.append(gpu_product.id)

    psu_spec = getattr(psu_product, "psu_spec", None)
    if not psu_spec or getattr(psu_spec, "wattage", None) is None:
        return (
            RuleCheckResult(
                rule=RuleIdentifier.PSU_CAPACITY.value,
                status=RuleStatus.WARNING,
                message="Compatibility could not be fully verified because PSU wattage specification is missing.",
                component_ids=comp_ids,
            ),
            None,
            None,
        )

    psu_wattage = psu_spec.wattage

    # Validate CPU TDP if CPU is present
    cpu_tdp = 0
    if cpu_product:
        cpu_spec = getattr(cpu_product, "cpu_spec", None)
        if not cpu_spec or getattr(cpu_spec, "tdp_watts", None) is None:
            return (
                RuleCheckResult(
                    rule=RuleIdentifier.PSU_CAPACITY.value,
                    status=RuleStatus.WARNING,
                    message="Compatibility could not be fully verified because CPU power specification (TDP) is missing.",
                    component_ids=comp_ids,
                    actual=f"PSU: {psu_wattage}W",
                    expected="Authoritative CPU TDP",
                ),
                None,
                None,
            )
        cpu_tdp = cpu_spec.tdp_watts

    # Validate GPU TDP if GPU is present
    gpu_tdp = 0
    if gpu_product:
        gpu_spec = getattr(gpu_product, "gpu_spec", None)
        if not gpu_spec or getattr(gpu_spec, "tdp_watts", None) is None:
            return (
                RuleCheckResult(
                    rule=RuleIdentifier.PSU_CAPACITY.value,
                    status=RuleStatus.WARNING,
                    message="Compatibility could not be fully verified because GPU power specification (TDP) is missing.",
                    component_ids=comp_ids,
                    actual=f"PSU: {psu_wattage}W",
                    expected="Authoritative GPU TDP",
                ),
                None,
                None,
            )
        gpu_tdp = gpu_spec.tdp_watts

    # If neither CPU nor GPU is present, power cannot be meaningfully checked
    if not cpu_product and not gpu_product:
        return (
            RuleCheckResult(
                rule=RuleIdentifier.PSU_CAPACITY.value,
                status=RuleStatus.WARNING,
                message="Compatibility could not be fully verified because no CPU or GPU is selected to calculate required system wattage.",
                component_ids=comp_ids,
                actual=f"PSU: {psu_wattage}W",
                expected="CPU and/or GPU",
            ),
            None,
            None,
        )

    estimated_system_power = cpu_tdp + gpu_tdp + BASE_SYSTEM_ALLOWANCE_WATTS
    required_psu_wattage = int(math.ceil(estimated_system_power * SAFETY_MARGIN_MULTIPLIER))

    if psu_wattage >= required_psu_wattage:
        return (
            RuleCheckResult(
                rule=RuleIdentifier.PSU_CAPACITY.value,
                status=RuleStatus.PASS,
                message=(
                    f"PSU capacity ({psu_wattage}W) meets or exceeds calculated system requirement "
                    f"({required_psu_wattage}W, based on {estimated_system_power}W estimated load with 25% safety margin)."
                ),
                component_ids=comp_ids,
                actual=f"{psu_wattage}W",
                expected=f">= {required_psu_wattage}W",
            ),
            estimated_system_power,
            required_psu_wattage,
        )
    else:
        return (
            RuleCheckResult(
                rule=RuleIdentifier.PSU_CAPACITY.value,
                status=RuleStatus.FAIL,
                message=(
                    f"Insufficient PSU capacity: selected PSU provides {psu_wattage}W, but estimated system "
                    f"requirement is {required_psu_wattage}W ({estimated_system_power}W estimated load + 25% safety margin)."
                ),
                component_ids=comp_ids,
                actual=f"{psu_wattage}W",
                expected=f">= {required_psu_wattage}W",
            ),
            estimated_system_power,
            required_psu_wattage,
        )


def check_cooler_cpu(
    cooler_product: Product,
    cpu_product: Product,
) -> RuleCheckResult:
    """
    Evaluates cooler socket compatibility with CPU.
    Rule: CPU.socket in Cooler.supported_sockets
    """
    comp_ids = [cooler_product.id, cpu_product.id]
    cooler_spec = getattr(cooler_product, "cooling_spec", None)
    cpu_spec = getattr(cpu_product, "cpu_spec", None)

    if not cooler_spec or not cooler_spec.supported_sockets or not cpu_spec or not cpu_spec.socket:
        return RuleCheckResult(
            rule=RuleIdentifier.COOLER_SOCKET.value,
            status=RuleStatus.WARNING,
            message="Compatibility could not be fully verified because CPU cooler supported sockets or CPU socket specification is missing.",
            component_ids=comp_ids,
        )

    norm_cpu_socket = _normalize_string(cpu_spec.socket)
    norm_sockets = [_normalize_string(s) for s in cooler_spec.supported_sockets] if isinstance(cooler_spec.supported_sockets, list) else [_normalize_string(str(cooler_spec.supported_sockets))]

    if norm_cpu_socket in norm_sockets:
        return RuleCheckResult(
            rule=RuleIdentifier.COOLER_SOCKET.value,
            status=RuleStatus.PASS,
            message=f"CPU socket ({cpu_spec.socket}) is supported by CPU cooler.",
            component_ids=comp_ids,
            actual=cpu_spec.socket,
            expected=cooler_spec.supported_sockets,
        )
    else:
        sockets_str = ", ".join(cooler_spec.supported_sockets) if isinstance(cooler_spec.supported_sockets, list) else str(cooler_spec.supported_sockets)
        return RuleCheckResult(
            rule=RuleIdentifier.COOLER_SOCKET.value,
            status=RuleStatus.FAIL,
            message=f"CPU socket '{cpu_spec.socket}' is not supported by CPU cooler (supported: {sockets_str}).",
            component_ids=comp_ids,
            actual=cpu_spec.socket,
            expected=cooler_spec.supported_sockets,
        )


def check_cooler_case(
    cooler_product: Product,
    case_product: Product,
) -> RuleCheckResult:
    """
    Evaluates physical CPU cooler height clearance inside Case.
    Rule: Cooler.height_mm <= Case.max_cpu_cooler_height_mm
    """
    comp_ids = [cooler_product.id, case_product.id]
    cooler_spec = getattr(cooler_product, "cooling_spec", None)
    case_spec = getattr(case_product, "case_spec", None)

    if not cooler_spec or not cooler_spec.height_mm or not case_spec or not case_spec.max_cpu_cooler_height_mm:
        return RuleCheckResult(
            rule=RuleIdentifier.COOLER_CASE_HEIGHT.value,
            status=RuleStatus.WARNING,
            message="Compatibility could not be fully verified because CPU cooler height or case clearance specification is missing.",
            component_ids=comp_ids,
        )

    if cooler_spec.height_mm <= case_spec.max_cpu_cooler_height_mm:
        return RuleCheckResult(
            rule=RuleIdentifier.COOLER_CASE_HEIGHT.value,
            status=RuleStatus.PASS,
            message=f"CPU cooler height ({cooler_spec.height_mm} mm) fits within case maximum cooler clearance ({case_spec.max_cpu_cooler_height_mm} mm).",
            component_ids=comp_ids,
            actual=f"{cooler_spec.height_mm} mm",
            expected=f"<= {case_spec.max_cpu_cooler_height_mm} mm",
        )
    else:
        return RuleCheckResult(
            rule=RuleIdentifier.COOLER_CASE_HEIGHT.value,
            status=RuleStatus.FAIL,
            message=f"CPU cooler height ({cooler_spec.height_mm} mm) exceeds case maximum cooler clearance ({case_spec.max_cpu_cooler_height_mm} mm).",
            component_ids=comp_ids,
            actual=f"{cooler_spec.height_mm} mm",
            expected=f"<= {case_spec.max_cpu_cooler_height_mm} mm",
        )
