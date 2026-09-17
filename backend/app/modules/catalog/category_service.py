from typing import List, Optional
from app.core import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.catalog.category_model import Category
from app.modules.catalog.category_schemas import (
    CategoryCreateRequest,
    CategoryUpdateRequest,
)
from app.modules.products.models import Product
from app.utils.slug import slugify


def list_categories(
    db: Session,
    include_inactive: bool = False,
    search: Optional[str] = None,
) -> List[Category]:
    """
    Returns categories sorted alphabetically by name.
    Public requests only receive active categories.
    """
    query = db.query(Category)
    if not include_inactive:
        query = query.filter(Category.is_active.is_(True))

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            Category.name.ilike(search_term) | Category.description.ilike(search_term)
        )

    return query.order_by(Category.name.asc()).all()


def get_category_by_id(
    db: Session,
    category_id: int,
    include_inactive: bool = False,
) -> Optional[Category]:
    """
    Retrieves a category by primary key.
    """
    query = db.query(Category).filter(Category.id == category_id)
    if not include_inactive:
        query = query.filter(Category.is_active.is_(True))
    return query.first()


def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    """
    Case-insensitive lookup by category name.
    """
    normalized_name = name.strip().lower()
    return (
        db.query(Category)
        .filter(func.lower(Category.name) == normalized_name)
        .first()
    )


def get_category_by_slug(db: Session, slug: str) -> Optional[Category]:
    """
    Lookup category by unique slug.
    """
    return db.query(Category).filter(Category.slug == slug.strip().lower()).first()


def create_category(
    db: Session,
    category_in: CategoryCreateRequest,
) -> Category:
    """
    Creates a new category with a deterministic slug.
    Validates against duplicate names and slugs.
    """
    trimmed_name = category_in.name.strip()
    if get_category_by_name(db, trimmed_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A category named '{trimmed_name}' already exists.",
        )

    generated_slug = slugify(trimmed_name)
    if not generated_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name must contain valid alphanumeric characters to generate a slug.",
        )

    if get_category_by_slug(db, generated_slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A category with slug '{generated_slug}' already exists.",
        )

    category = Category(
        name=trimmed_name,
        slug=generated_slug,
        description=category_in.description.strip() if category_in.description else None,
        is_active=category_in.is_active if category_in.is_active is not None else True,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(
    db: Session,
    category_id: int,
    category_in: CategoryUpdateRequest,
) -> Category:
    """
    Updates an existing category.
    Regenerates slug and validates uniqueness if name is modified.
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )

    if category_in.name is not None:
        new_name = category_in.name.strip()
        if new_name.lower() != category.name.lower():
            existing_named = get_category_by_name(db, new_name)
            if existing_named and existing_named.id != category.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A category named '{new_name}' already exists.",
                )

            new_slug = slugify(new_name)
            if not new_slug:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category name must contain valid alphanumeric characters to generate a slug.",
                )

            existing_slugged = get_category_by_slug(db, new_slug)
            if existing_slugged and existing_slugged.id != category.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A category with slug '{new_slug}' already exists.",
                )

            category.name = new_name
            category.slug = new_slug

    if category_in.description is not None:
        category.description = (
            category_in.description.strip() if category_in.description else None
        )

    if category_in.is_active is not None:
        category.is_active = category_in.is_active

    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    """
    Deletes a category record if no products are associated with it.
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        )

    # Module 3 delete-safety check: prevent hard deletion if products exist
    product_count = db.query(Product).filter(Product.category_id == category_id).count()
    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category '{category.name}' because {product_count} product(s) are attached to it. Please deactivate the category instead or reassign its products.",
        )

    db.delete(category)
    db.commit()
