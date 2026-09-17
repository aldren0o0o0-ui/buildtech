from typing import List, Optional
from app.core import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.catalog.brand_model import Brand
from app.modules.catalog.brand_schemas import BrandCreateRequest, BrandUpdateRequest
from app.modules.products.models import Product
from app.utils.slug import slugify


def list_brands(
    db: Session,
    include_inactive: bool = False,
    search: Optional[str] = None,
) -> List[Brand]:
    """
    Returns brands sorted alphabetically by name.
    Public requests only receive active brands.
    """
    query = db.query(Brand)
    if not include_inactive:
        query = query.filter(Brand.is_active.is_(True))

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            Brand.name.ilike(search_term) | Brand.description.ilike(search_term)
        )

    return query.order_by(Brand.name.asc()).all()


def get_brand_by_id(
    db: Session,
    brand_id: int,
    include_inactive: bool = False,
) -> Optional[Brand]:
    """
    Retrieves a brand by primary key.
    """
    query = db.query(Brand).filter(Brand.id == brand_id)
    if not include_inactive:
        query = query.filter(Brand.is_active.is_(True))
    return query.first()


def get_brand_by_name(db: Session, name: str) -> Optional[Brand]:
    """
    Case-insensitive lookup by brand name.
    """
    normalized_name = name.strip().lower()
    return (
        db.query(Brand)
        .filter(func.lower(Brand.name) == normalized_name)
        .first()
    )


def get_brand_by_slug(db: Session, slug: str) -> Optional[Brand]:
    """
    Lookup brand by unique slug.
    """
    return db.query(Brand).filter(Brand.slug == slug.strip().lower()).first()


def create_brand(
    db: Session,
    brand_in: BrandCreateRequest,
) -> Brand:
    """
    Creates a new brand with a deterministic slug.
    Validates against duplicate names and slugs.
    """
    trimmed_name = brand_in.name.strip()
    if get_brand_by_name(db, trimmed_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A brand named '{trimmed_name}' already exists.",
        )

    generated_slug = slugify(trimmed_name)
    if not generated_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brand name must contain valid alphanumeric characters to generate a slug.",
        )

    if get_brand_by_slug(db, generated_slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A brand with slug '{generated_slug}' already exists.",
        )

    brand = Brand(
        name=trimmed_name,
        slug=generated_slug,
        description=brand_in.description.strip() if brand_in.description else None,
        logo_url=brand_in.logo_url.strip() if brand_in.logo_url else None,
        is_active=brand_in.is_active if brand_in.is_active is not None else True,
    )
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


def update_brand(
    db: Session,
    brand_id: int,
    brand_in: BrandUpdateRequest,
) -> Brand:
    """
    Updates an existing brand.
    Regenerates slug and validates uniqueness if name is modified.
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found.",
        )

    if brand_in.name is not None:
        new_name = brand_in.name.strip()
        if new_name.lower() != brand.name.lower():
            existing_named = get_brand_by_name(db, new_name)
            if existing_named and existing_named.id != brand.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A brand named '{new_name}' already exists.",
                )

            new_slug = slugify(new_name)
            if not new_slug:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Brand name must contain valid alphanumeric characters to generate a slug.",
                )

            existing_slugged = get_brand_by_slug(db, new_slug)
            if existing_slugged and existing_slugged.id != brand.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A brand with slug '{new_slug}' already exists.",
                )

            brand.name = new_name
            brand.slug = new_slug

    if brand_in.description is not None:
        brand.description = (
            brand_in.description.strip() if brand_in.description else None
        )

    if brand_in.logo_url is not None:
        brand.logo_url = brand_in.logo_url.strip() if brand_in.logo_url else None

    if brand_in.is_active is not None:
        brand.is_active = brand_in.is_active

    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


def delete_brand(db: Session, brand_id: int) -> None:
    """
    Deletes a brand record if no products are associated with it.
    """
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found.",
        )

    # Module 3 delete-safety check: prevent hard deletion if products exist
    product_count = db.query(Product).filter(Product.brand_id == brand_id).count()
    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete brand '{brand.name}' because {product_count} product(s) are attached to it. Please deactivate the brand instead or reassign its products.",
        )

    db.delete(brand)
    db.commit()
