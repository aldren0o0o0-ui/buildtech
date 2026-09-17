"""
Compatibility Engine Schemas (Module 14).

Defines deterministic validation schemas, rule status semantics,
and customer-safe API response models.
"""

from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RuleStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class RuleIdentifier(str, Enum):
    CPU_SOCKET = "CPU_SOCKET"
    RAM_TYPE = "RAM_TYPE"
    RAM_SPEED = "RAM_SPEED"
    GPU_CASE_CLEARANCE = "GPU_CASE_CLEARANCE"
    MOTHERBOARD_FORM_FACTOR = "MOTHERBOARD_FORM_FACTOR"
    STORAGE_INTERFACE = "STORAGE_INTERFACE"
    PSU_CAPACITY = "PSU_CAPACITY"
    COOLER_SOCKET = "COOLER_SOCKET"
    COOLER_CASE_HEIGHT = "COOLER_CASE_HEIGHT"


class RuleCheckResult(BaseModel):
    rule: str
    status: RuleStatus
    message: str
    component_ids: Optional[List[int]] = None
    actual: Optional[Any] = None
    expected: Optional[Any] = None

    model_config = ConfigDict(from_attributes=True)


class ComponentSummary(BaseModel):
    product_id: int
    sku: str
    name: str
    category_name: Optional[str] = None
    hardware_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CompatibilityCheckRequest(BaseModel):
    product_ids: List[int] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Authoritative product IDs to evaluate for compatibility.",
    )

    model_config = ConfigDict(extra="forbid")


class CompatibilityResponse(BaseModel):
    status: RuleStatus
    summary: str
    component_count: int
    pass_count: int
    warning_count: int
    fail_count: int
    estimated_system_power_watts: Optional[int] = None
    required_psu_watts: Optional[int] = None
    components: List[ComponentSummary] = Field(default_factory=list)
    checks: List[RuleCheckResult] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
