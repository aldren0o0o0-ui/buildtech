from datetime import datetime
from decimal import Decimal
from typing import Any, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==========================================
# 1. CPU SPECIFICATION SCHEMAS
# ==========================================

class CpuSpecificationRequest(BaseModel):
    socket: str = Field(..., min_length=1, max_length=50)
    core_count: int = Field(..., gt=0)
    thread_count: int = Field(..., gt=0)
    base_clock_ghz: Decimal = Field(..., ge=0, decimal_places=2, max_digits=4)
    boost_clock_ghz: Decimal = Field(..., ge=0, decimal_places=2, max_digits=4)
    tdp_watts: int = Field(..., ge=0)
    architecture: Optional[str] = Field(None, max_length=100)
    integrated_graphics: Optional[str] = Field(None, max_length=100)

    @field_validator("socket", mode="before")
    @classmethod
    def strip_socket(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Socket cannot be empty.")
        return v

    @field_validator("architecture", "integrated_graphics", mode="before")
    @classmethod
    def strip_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v = v.strip()
            if not v:
                return None
        return v

    model_config = ConfigDict(extra="forbid")


class CpuSpecificationResponse(BaseModel):
    id: int
    product_id: int
    socket: str
    core_count: int
    thread_count: int
    base_clock_ghz: Decimal
    boost_clock_ghz: Decimal
    tdp_watts: int
    architecture: Optional[str] = None
    integrated_graphics: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. GPU SPECIFICATION SCHEMAS
# ==========================================

class GpuSpecificationRequest(BaseModel):
    chipset: str = Field(..., min_length=1, max_length=100)
    vram_gb: int = Field(..., gt=0)
    memory_type: str = Field(..., min_length=1, max_length=50)
    core_clock_mhz: Optional[int] = Field(None, ge=0)
    boost_clock_mhz: int = Field(..., ge=0)
    length_mm: int = Field(..., ge=0)
    tdp_watts: int = Field(..., ge=0)
    recommended_psu_watts: int = Field(..., ge=0)

    @field_validator("chipset", "memory_type", mode="before")
    @classmethod
    def strip_required_strings(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty.")
        return v

    model_config = ConfigDict(extra="forbid")


class GpuSpecificationResponse(BaseModel):
    id: int
    product_id: int
    chipset: str
    vram_gb: int
    memory_type: str
    core_clock_mhz: Optional[int] = None
    boost_clock_mhz: int
    length_mm: int
    tdp_watts: int
    recommended_psu_watts: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 3. MOTHERBOARD SPECIFICATION SCHEMAS
# ==========================================

class MotherboardSpecificationRequest(BaseModel):
    socket: str = Field(..., min_length=1, max_length=50)
    chipset: str = Field(..., min_length=1, max_length=50)
    form_factor: str = Field(..., min_length=1, max_length=50)
    memory_type: str = Field(..., min_length=1, max_length=50)
    memory_slots: int = Field(..., gt=0)
    max_memory_gb: int = Field(..., gt=0)
    pcie_version: Optional[str] = Field(None, max_length=50)
    wifi: bool = False
    max_memory_speed_mhz: Optional[int] = Field(None, ge=0)
    supported_storage_interfaces: Optional[List[str]] = Field(None)

    @field_validator("socket", "chipset", "form_factor", "memory_type", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty.")
        return v

    @field_validator("pcie_version", mode="before")
    @classmethod
    def strip_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v = v.strip()
            if not v:
                return None
        return v

    model_config = ConfigDict(extra="forbid")


class MotherboardSpecificationResponse(BaseModel):
    id: int
    product_id: int
    socket: str
    chipset: str
    form_factor: str
    memory_type: str
    memory_slots: int
    max_memory_gb: int
    pcie_version: Optional[str] = None
    wifi: bool
    max_memory_speed_mhz: Optional[int] = None
    supported_storage_interfaces: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 4. MEMORY SPECIFICATION SCHEMAS
# ==========================================

class MemorySpecificationRequest(BaseModel):
    memory_type: str = Field(..., min_length=1, max_length=50)
    capacity_gb: int = Field(..., gt=0)
    speed_mhz: int = Field(..., gt=0)
    module_count: int = Field(..., gt=0)
    cas_latency: Optional[int] = Field(None, gt=0)

    @field_validator("memory_type", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Memory type cannot be empty.")
        return v

    model_config = ConfigDict(extra="forbid")


class MemorySpecificationResponse(BaseModel):
    id: int
    product_id: int
    memory_type: str
    capacity_gb: int
    speed_mhz: int
    module_count: int
    cas_latency: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 5. STORAGE SPECIFICATION SCHEMAS
# ==========================================

class StorageSpecificationRequest(BaseModel):
    storage_type: str = Field(..., min_length=1, max_length=50)
    capacity_gb: int = Field(..., gt=0)
    interface: str = Field(..., min_length=1, max_length=50)
    form_factor: str = Field(..., min_length=1, max_length=50)
    read_speed_mbps: Optional[int] = Field(None, ge=0)
    write_speed_mbps: Optional[int] = Field(None, ge=0)

    @field_validator("storage_type", "interface", "form_factor", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty.")
        return v

    model_config = ConfigDict(extra="forbid")


class StorageSpecificationResponse(BaseModel):
    id: int
    product_id: int
    storage_type: str
    capacity_gb: int
    interface: str
    form_factor: str
    read_speed_mbps: Optional[int] = None
    write_speed_mbps: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 6. PSU SPECIFICATION SCHEMAS
# ==========================================

class PsuSpecificationRequest(BaseModel):
    wattage: int = Field(..., gt=0)
    efficiency_rating: str = Field(..., min_length=1, max_length=50)
    modularity: str = Field(..., min_length=1, max_length=50)
    form_factor: str = Field(..., min_length=1, max_length=50)

    @field_validator("efficiency_rating", "modularity", "form_factor", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty.")
        return v

    model_config = ConfigDict(extra="forbid")


class PsuSpecificationResponse(BaseModel):
    id: int
    product_id: int
    wattage: int
    efficiency_rating: str
    modularity: str
    form_factor: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 7. CASE SPECIFICATION SCHEMAS
# ==========================================

class CaseSpecificationRequest(BaseModel):
    case_type: str = Field(..., min_length=1, max_length=50)
    supported_motherboard_form_factors: List[str] = Field(..., min_length=1)
    max_gpu_length_mm: int = Field(..., gt=0)
    max_cpu_cooler_height_mm: int = Field(..., gt=0)
    psu_form_factor: str = Field(..., min_length=1, max_length=50)
    drive_bays: Optional[str] = Field(None, max_length=100)

    @field_validator("case_type", "psu_form_factor", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty.")
        return v

    @field_validator("drive_bays", mode="before")
    @classmethod
    def strip_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and isinstance(v, str):
            v = v.strip()
            if not v:
                return None
        return v

    model_config = ConfigDict(extra="forbid")


class CaseSpecificationResponse(BaseModel):
    id: int
    product_id: int
    case_type: str
    supported_motherboard_form_factors: List[str]
    max_gpu_length_mm: int
    max_cpu_cooler_height_mm: int
    psu_form_factor: str
    drive_bays: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 8. COOLING SPECIFICATION SCHEMAS
# ==========================================

class CoolingSpecificationRequest(BaseModel):
    cooler_type: str = Field(..., min_length=1, max_length=50)
    supported_sockets: List[str] = Field(..., min_length=1)
    radiator_size_mm: Optional[int] = Field(None, gt=0)
    fan_size_mm: Optional[int] = Field(None, gt=0)
    max_tdp_watts: Optional[int] = Field(None, ge=0)
    height_mm: int = Field(..., gt=0)

    @field_validator("cooler_type", mode="before")
    @classmethod
    def strip_strings(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Cooler type cannot be empty.")
        return v

    model_config = ConfigDict(extra="forbid")


class CoolingSpecificationResponse(BaseModel):
    id: int
    product_id: int
    cooler_type: str
    supported_sockets: List[str]
    radiator_size_mm: Optional[int] = None
    fan_size_mm: Optional[int] = None
    max_tdp_watts: Optional[int] = None
    height_mm: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# UNIFIED SPECIFICATION WRAPPER RESPONSE
# ==========================================

SpecificationDataUnion = Union[
    CpuSpecificationResponse,
    GpuSpecificationResponse,
    MotherboardSpecificationResponse,
    MemorySpecificationResponse,
    StorageSpecificationResponse,
    PsuSpecificationResponse,
    CaseSpecificationResponse,
    CoolingSpecificationResponse,
]


class ProductSpecificationResponse(BaseModel):
    type: str
    data: Optional[SpecificationDataUnion] = None
