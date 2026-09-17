from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from app.core import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.products.models import Product, ProductStatus
from app.modules.products.query_builder import ProductQueryBuilder
from app.modules.products.schemas import ProductCreateRequest, ProductUpdateRequest
from app.utils.slug import slugify


def list_products(
    db: Session,
    include_inactive: bool = False,
    status_filter: Optional[str] = None,
    category_id: Optional[int] = None,
    category: Optional[str] = None,
    brand_id: Optional[int] = None,
    brand: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    search: Optional[str] = None,
    in_stock: Optional[bool] = None,
    socket: Optional[str] = None,
    cores_min: Optional[int] = None,
    threads_min: Optional[int] = None,
    tdp_max: Optional[int] = None,
    vram_min: Optional[int] = None,
    gpu_chipset: Optional[str] = None,
    gpu_memory_type: Optional[str] = None,
    form_factor: Optional[str] = None,
    memory_type: Optional[str] = None,
    capacity_min: Optional[int] = None,
    storage_type: Optional[str] = None,
    wattage_min: Optional[int] = None,
    efficiency_rating: Optional[str] = None,
    case_type: Optional[str] = None,
    cooler_type: Optional[str] = None,
    sort: Optional[str] = "newest",
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Union[List[Product], Dict[str, Any]]:
    """
    Retrieves products with composable storefront search, category, brand,
    price range, stock availability, category-specific specification filters,
    controlled sorting, and optional server-side pagination.
    """
    builder = (
        ProductQueryBuilder(
            db=db,
            include_inactive=include_inactive,
            status_filter=status_filter,
        )
        .apply_search(search)
        .apply_category(category_id=category_id, category_slug=category)
        .apply_brand(brand_id=brand_id, brand_slug=brand)
        .apply_price_range(min_price=min_price, max_price=max_price)
        .apply_availability(in_stock=in_stock)
        .apply_specifications(
            socket=socket,
            cores_min=cores_min,
            threads_min=threads_min,
            tdp_max=tdp_max,
            vram_min=vram_min,
            gpu_chipset=gpu_chipset,
            gpu_memory_type=gpu_memory_type,
            form_factor=form_factor,
            memory_type=memory_type,
            capacity_min=capacity_min,
            storage_type=storage_type,
            wattage_min=wattage_min,
            efficiency_rating=efficiency_rating,
            case_type=case_type,
            cooler_type=cooler_type,
        )
        .apply_sorting(sort)
    )

    return builder.execute(page=page, page_size=page_size)


def get_product_by_id(
    db: Session,
    product_id: int,
    include_inactive: bool = False,
) -> Optional[Product]:
    """
    Retrieves a product by primary key with eager loaded relationships.
    """
    query = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.brand))
        .filter(Product.id == product_id)
    )
    if not include_inactive:
        query = query.filter(
            Product.is_active.is_(True),
            Product.status == ProductStatus.ACTIVE.value,
        )
    return query.first()


def get_product_by_slug(
    db: Session,
    slug: str,
    include_inactive: bool = False,
) -> Optional[Product]:
    """
    Retrieves a product by unique slug with eager loaded relationships.
    """
    query = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.brand))
        .filter(Product.slug == slug.strip().lower())
    )
    if not include_inactive:
        query = query.filter(
            Product.is_active.is_(True),
            Product.status == ProductStatus.ACTIVE.value,
        )
    return query.first()


def get_product_by_sku(db: Session, sku: str) -> Optional[Product]:
    """
    Retrieves a product by exact SKU (case-insensitive).
    """
    return (
        db.query(Product)
        .filter(func.lower(Product.sku) == sku.strip().lower())
        .first()
    )


def create_product(
    db: Session,
    product_in: ProductCreateRequest,
) -> Product:
    """
    Creates a new product record.
    Validates Category existence/status, Brand existence/status, SKU uniqueness, and slug generation.
    """
    # 1. Validate Category
    category = db.query(Category).filter(Category.id == product_in.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with ID {product_in.category_id} does not exist.",
        )
    if not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{category.name}' is inactive and cannot be assigned to new products.",
        )

    # 2. Validate Brand
    brand = db.query(Brand).filter(Brand.id == product_in.brand_id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Brand with ID {product_in.brand_id} does not exist.",
        )
    if not brand.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Brand '{brand.name}' is inactive and cannot be assigned to new products.",
        )

    # 3. Validate SKU uniqueness
    trimmed_sku = product_in.sku.strip()
    if get_product_by_sku(db, trimmed_sku):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A product with SKU '{trimmed_sku}' already exists.",
        )

    # 4. Generate and validate slug
    trimmed_name = product_in.name.strip()
    generated_slug = slugify(trimmed_name)
    if not generated_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product name must contain valid alphanumeric characters to generate a slug.",
        )

    existing_slug_product = get_product_by_slug(db, generated_slug, include_inactive=True)
    if existing_slug_product:
        # Append SKU suffix to ensure uniqueness if name collides
        generated_slug = f"{generated_slug}-{slugify(trimmed_sku)}"
        if get_product_by_slug(db, generated_slug, include_inactive=True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A product with slug '{generated_slug}' already exists.",
            )

    product = Product(
        sku=trimmed_sku,
        name=trimmed_name,
        slug=generated_slug,
        description=product_in.description,
        category_id=product_in.category_id,
        brand_id=product_in.brand_id,
        price=product_in.price,
        image_url=product_in.image_url,
        status=product_in.status.value if product_in.status else ProductStatus.ACTIVE.value,
        is_active=product_in.is_active if product_in.is_active is not None else True,
    )

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(
    db: Session,
    product_id: int,
    product_in: ProductUpdateRequest,
) -> Product:
    """
    Updates an existing product record.
    """
    product = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.brand))
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    # 1. Update SKU if changed
    if product_in.sku is not None:
        new_sku = product_in.sku.strip()
        if new_sku.lower() != product.sku.lower():
            existing_sku = get_product_by_sku(db, new_sku)
            if existing_sku and existing_sku.id != product.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A product with SKU '{new_sku}' already exists.",
                )
            product.sku = new_sku

    # 2. Update Name and regenerate Slug if changed
    if product_in.name is not None:
        new_name = product_in.name.strip()
        if new_name.lower() != product.name.lower():
            new_slug = slugify(new_name)
            if not new_slug:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product name must contain valid alphanumeric characters to generate a slug.",
                )
            existing_slug = get_product_by_slug(db, new_slug, include_inactive=True)
            if existing_slug and existing_slug.id != product.id:
                new_slug = f"{new_slug}-{slugify(product.sku)}"
                existing_slug = get_product_by_slug(db, new_slug, include_inactive=True)
                if existing_slug and existing_slug.id != product.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"A product with slug '{new_slug}' already exists.",
                    )
            product.name = new_name
            product.slug = new_slug

    # 3. Update Category if changed
    if product_in.category_id is not None and product_in.category_id != product.category_id:
        category = db.query(Category).filter(Category.id == product_in.category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {product_in.category_id} does not exist.",
            )
        product.category_id = product_in.category_id

    # 4. Update Brand if changed
    if product_in.brand_id is not None and product_in.brand_id != product.brand_id:
        brand = db.query(Brand).filter(Brand.id == product_in.brand_id).first()
        if not brand:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Brand with ID {product_in.brand_id} does not exist.",
            )
        product.brand_id = product_in.brand_id

    # 5. Update other fields
    if product_in.description is not None:
        product.description = product_in.description
    if product_in.price is not None:
        product.price = product_in.price
    if product_in.image_url is not None:
        product.image_url = product_in.image_url
    if product_in.status is not None:
        product.status = product_in.status.value
    if product_in.is_active is not None:
        product.is_active = product_in.is_active

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> None:
    """
    Permanently deletes a product from the database.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    db.delete(product)
    db.commit()
