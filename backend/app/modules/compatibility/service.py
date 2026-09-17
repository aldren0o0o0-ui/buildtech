"""
Compatibility Engine Service (Module 14).

Orchestrates deterministic rule evaluation over authoritative PostgreSQL product specifications
in application memory. Guarantees pure read-only operations and strictly deterministic outputs.
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.modules.catalog.category_model import Category
from app.modules.compatibility.repository import CompatibilityRepository
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
from app.modules.compatibility.schemas import (
    CompatibilityCheckRequest,
    CompatibilityResponse,
    ComponentSummary,
    RuleCheckResult,
    RuleIdentifier,
    RuleStatus,
)
from app.modules.products.models import Product
from app.modules.products.specifications.service import resolve_hardware_type

# Stable deterministic rule ordering
STABLE_RULE_ORDER = [
    RuleIdentifier.CPU_SOCKET.value,
    RuleIdentifier.RAM_TYPE.value,
    RuleIdentifier.RAM_SPEED.value,
    RuleIdentifier.GPU_CASE_CLEARANCE.value,
    RuleIdentifier.MOTHERBOARD_FORM_FACTOR.value,
    RuleIdentifier.STORAGE_INTERFACE.value,
    RuleIdentifier.PSU_CAPACITY.value,
    RuleIdentifier.COOLER_SOCKET.value,
    RuleIdentifier.COOLER_CASE_HEIGHT.value,
]


def _classify_hardware_type(product: Product) -> Optional[str]:
    """Classifies a product into a hardware category using spec or category."""
    if product.cpu_spec:
        return "CPU"
    if product.gpu_spec:
        return "GPU"
    if product.motherboard_spec:
        return "MOTHERBOARD"
    if product.memory_spec:
        return "MEMORY"
    if product.storage_spec:
        return "STORAGE"
    if product.psu_spec:
        return "PSU"
    if product.case_spec:
        return "CASE"
    if product.cooling_spec:
        return "COOLING"

    if product.category:
        return resolve_hardware_type(product.category)

    return None


class CompatibilityService:
    """Deterministic domain service for PC hardware compatibility verification."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = CompatibilityRepository(db)

    def check_compatibility(
        self,
        request: CompatibilityCheckRequest,
    ) -> CompatibilityResponse:
        """
        Evaluates compatibility across all selected products using authoritative PostgreSQL data.
        Returns aggregated PASS / WARNING / FAIL results with stable ordering.
        """
        products = self.repository.get_products_by_ids(request.product_ids)

        # Categorize components
        categorized: Dict[str, List[Product]] = {
            "CPU": [],
            "GPU": [],
            "MOTHERBOARD": [],
            "MEMORY": [],
            "STORAGE": [],
            "PSU": [],
            "CASE": [],
            "COOLING": [],
        }

        components: List[ComponentSummary] = []
        for product in products:
            hw_type = _classify_hardware_type(product)
            if hw_type and hw_type in categorized:
                categorized[hw_type].append(product)

            cat_name = product.category.name if product.category else None
            components.append(
                ComponentSummary(
                    product_id=product.id,
                    sku=product.sku,
                    name=product.name,
                    category_name=cat_name,
                    hardware_type=hw_type,
                )
            )

        checks: List[RuleCheckResult] = []
        estimated_system_power: Optional[int] = None
        required_psu: Optional[int] = None

        cpus = categorized["CPU"]
        gpus = categorized["GPU"]
        mobos = categorized["MOTHERBOARD"]
        rams = categorized["MEMORY"]
        storages = categorized["STORAGE"]
        psus = categorized["PSU"]
        cases = categorized["CASE"]
        coolers = categorized["COOLING"]

        # 1. CPU <-> Motherboard
        for cpu in cpus:
            for mb in mobos:
                checks.append(check_cpu_motherboard(cpu, mb))

        # 2. RAM <-> Motherboard
        for ram in rams:
            for mb in mobos:
                checks.append(check_ram_motherboard(ram, mb))
                checks.append(check_ram_speed(ram, mb))

        # 3. GPU <-> Case
        for gpu in gpus:
            for case in cases:
                checks.append(check_gpu_case(gpu, case))

        # 4. Motherboard <-> Case
        for mb in mobos:
            for case in cases:
                checks.append(check_motherboard_case(mb, case))

        # 5. Storage <-> Motherboard
        for storage in storages:
            for mb in mobos:
                checks.append(check_storage_motherboard(storage, mb))

        # 6. PSU <-> System Power
        for psu in psus:
            primary_cpu = cpus[0] if cpus else None
            primary_gpu = gpus[0] if gpus else None
            psu_result, est_power, req_psu = check_psu_capacity(psu, primary_cpu, primary_gpu)
            checks.append(psu_result)
            if est_power is not None:
                estimated_system_power = est_power
            if req_psu is not None:
                required_psu = req_psu

        # 7. Cooler <-> CPU & Cooler <-> Case
        for cooler in coolers:
            for cpu in cpus:
                checks.append(check_cooler_cpu(cooler, cpu))
            for case in cases:
                checks.append(check_cooler_case(cooler, case))

        # Deterministic sorting of checks by STABLE_RULE_ORDER, then by component_ids
        def _sort_key(c: RuleCheckResult):
            order_idx = STABLE_RULE_ORDER.index(c.rule) if c.rule in STABLE_RULE_ORDER else 99
            comp_key = tuple(c.component_ids or [])
            return (order_idx, comp_key)

        checks.sort(key=_sort_key)

        # Calculate counts
        pass_count = sum(1 for c in checks if c.status == RuleStatus.PASS)
        warning_count = sum(1 for c in checks if c.status == RuleStatus.WARNING)
        fail_count = sum(1 for c in checks if c.status == RuleStatus.FAIL)

        # Aggregate overall status
        if fail_count > 0:
            overall_status = RuleStatus.FAIL
            summary = "Selected components are incompatible. Please review the highlighted issues."
        elif warning_count > 0:
            overall_status = RuleStatus.WARNING
            summary = "Configuration has potential compatibility concerns or incomplete specifications."
        elif pass_count > 0:
            overall_status = RuleStatus.PASS
            summary = "All selected components are compatible."
        else:
            overall_status = RuleStatus.PASS
            summary = "No component conflicts detected for the selected configuration."

        return CompatibilityResponse(
            status=overall_status,
            summary=summary,
            component_count=len(products),
            pass_count=pass_count,
            warning_count=warning_count,
            fail_count=fail_count,
            estimated_system_power_watts=estimated_system_power,
            required_psu_watts=required_psu,
            components=components,
            checks=checks,
        )
