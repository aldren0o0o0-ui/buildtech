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
from app.modules.products.specifications.routes import router as specifications_router

__all__ = [
    "CpuSpecification",
    "GpuSpecification",
    "MotherboardSpecification",
    "MemorySpecification",
    "StorageSpecification",
    "PsuSpecification",
    "CaseSpecification",
    "CoolingSpecification",
    "specifications_router",
]
