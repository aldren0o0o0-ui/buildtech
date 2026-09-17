from typing import Any, Dict, Optional, Tuple
from app.core import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

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
from app.modules.products.specifications.schemas import (
    CaseSpecificationRequest,
    CoolingSpecificationRequest,
    CpuSpecificationRequest,
    GpuSpecificationRequest,
    MemorySpecificationRequest,
    MotherboardSpecificationRequest,
    PsuSpecificationRequest,
    StorageSpecificationRequest,
)

# Mapping of normalized Category keywords to Specification Types & Models
HARDWARE_TYPE_MAP = {
    "cpu": "CPU",
    "cpus": "CPU",
    "processor": "CPU",
    "processors": "CPU",
    "gpu": "GPU",
    "gpus": "GPU",
    "graphics-card": "GPU",
    "graphics-cards": "GPU",
    "video-card": "GPU",
    "video-cards": "GPU",
    "motherboard": "MOTHERBOARD",
    "motherboards": "MOTHERBOARD",
    "mainboard": "MOTHERBOARD",
    "mainboards": "MOTHERBOARD",
    "memory": "MEMORY",
    "ram": "MEMORY",
    "ddr4": "MEMORY",
    "ddr5": "MEMORY",
    "storage": "STORAGE",
    "ssd": "STORAGE",
    "ssds": "STORAGE",
    "hard-drive": "STORAGE",
    "hard-drives": "STORAGE",
    "psu": "PSU",
    "power-supply": "PSU",
    "power-supplies": "PSU",
    "case": "CASE",
    "cases": "CASE",
    "chassis": "CASE",
    "pc-case": "CASE",
    "pc-cases": "CASE",
    "cooling": "COOLING",
    "cooler": "COOLING",
    "coolers": "COOLING",
    "cpu-cooler": "COOLING",
    "cpu-coolers": "COOLING",
}


def resolve_hardware_type(category: Category) -> Optional[str]:
    """
    Resolves the hardware specification type from the Category's slug or name.
    """
    if not category:
        return None

    slug = (category.slug or "").lower().strip()
    if slug in HARDWARE_TYPE_MAP:
        return HARDWARE_TYPE_MAP[slug]

    name = (category.name or "").lower().strip().replace(" ", "-")
    if name in HARDWARE_TYPE_MAP:
        return HARDWARE_TYPE_MAP[name]

    # Partial keyword checks
    for key, hw_type in HARDWARE_TYPE_MAP.items():
        if key in slug or key in name:
            return hw_type

    return None


def get_specification_model_and_schema(hw_type: str) -> Tuple[Any, Any, str]:
    """
    Returns (ORM_Model, Pydantic_Request_Schema, Relationship_Attr_Name)
    """
    if hw_type == "CPU":
        return CpuSpecification, CpuSpecificationRequest, "cpu_spec"
    elif hw_type == "GPU":
        return GpuSpecification, GpuSpecificationRequest, "gpu_spec"
    elif hw_type == "MOTHERBOARD":
        return MotherboardSpecification, MotherboardSpecificationRequest, "motherboard_spec"
    elif hw_type == "MEMORY":
        return MemorySpecification, MemorySpecificationRequest, "memory_spec"
    elif hw_type == "STORAGE":
        return StorageSpecification, StorageSpecificationRequest, "storage_spec"
    elif hw_type == "PSU":
        return PsuSpecification, PsuSpecificationRequest, "psu_spec"
    elif hw_type == "CASE":
        return CaseSpecification, CaseSpecificationRequest, "case_spec"
    elif hw_type == "COOLING":
        return CoolingSpecification, CoolingSpecificationRequest, "cooling_spec"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported specification hardware type: {hw_type}",
        )


def get_product_for_specs(
    db: Session,
    product_id: int,
    include_inactive: bool = False,
) -> Product:
    """
    Helper to fetch product and enforce public visibility when required.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found.",
        )

    if not include_inactive:
        if not product.is_active or product.status != ProductStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or not currently available.",
            )

    return product


def get_product_specifications(
    db: Session,
    product_id: int,
    include_inactive: bool = False,
) -> Dict[str, Any]:
    """
    Retrieves the structured technical specifications for a product.
    """
    product = get_product_for_specs(db, product_id, include_inactive=include_inactive)
    category = db.query(Category).filter(Category.id == product.category_id).first()
    hw_type = resolve_hardware_type(category)

    if not hw_type:
        return {"type": "NONE", "data": None}

    model_cls, _, rel_attr = get_specification_model_and_schema(hw_type)
    spec_obj = db.query(model_cls).filter(model_cls.product_id == product.id).first()

    return {
        "type": hw_type,
        "data": spec_obj,
    }


def upsert_product_specifications(
    db: Session,
    product_id: int,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Creates or updates the specification record for a product.
    Strictly validates that the product's category matches the target specification model.
    """
    product = get_product_for_specs(db, product_id, include_inactive=True)
    category = db.query(Category).filter(Category.id == product.category_id).first()
    hw_type = resolve_hardware_type(category)

    if not hw_type:
        cat_name = category.name if category else "Unknown"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{cat_name}' does not support technical hardware specifications in Module 4.",
        )

    # If payload contains a 'type' field, verify it matches
    if "type" in payload and payload["type"]:
        payload_type = str(payload["type"]).strip().upper()
        if payload_type != hw_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Mismatched specification type: Product belongs to category '{category.name}' ({hw_type}), but received {payload_type} specifications.",
            )

    # Extract actual specification fields from payload if nested under 'data'
    raw_data = payload.get("data", payload) if isinstance(payload.get("data"), dict) else payload

    # Validate against category-specific Pydantic schema
    model_cls, schema_cls, _ = get_specification_model_and_schema(hw_type)
    try:
        validated_schema = schema_cls(**raw_data)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.errors(),
        )

    validated_dict = validated_schema.model_dump()

    # Query existing specification row
    existing_spec = db.query(model_cls).filter(model_cls.product_id == product.id).first()

    if existing_spec:
        # Update fields
        for field, val in validated_dict.items():
            setattr(existing_spec, field, val)
        db.add(existing_spec)
        db.commit()
        db.refresh(existing_spec)
        spec_result = existing_spec
    else:
        # Create new specification row
        new_spec = model_cls(product_id=product.id, **validated_dict)
        db.add(new_spec)
        db.commit()
        db.refresh(new_spec)
        spec_result = new_spec

    return {
        "type": hw_type,
        "data": spec_result,
    }


def delete_product_specifications(
    db: Session,
    product_id: int,
) -> None:
    """
    Deletes the specification record for a product without deleting the product itself.
    """
    product = get_product_for_specs(db, product_id, include_inactive=True)
    category = db.query(Category).filter(Category.id == product.category_id).first()
    hw_type = resolve_hardware_type(category)

    if not hw_type:
        return

    model_cls, _, _ = get_specification_model_and_schema(hw_type)
    spec_obj = db.query(model_cls).filter(model_cls.product_id == product.id).first()
    if spec_obj:
        db.delete(spec_obj)
        db.commit()
