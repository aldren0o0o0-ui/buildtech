from decimal import Decimal
from typing import List, Optional, Union
from app.core import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.schemas import MessageResponse
from app.db.session import get_db
from app.modules.auth.dependencies import get_optional_current_user, require_admin
from app.modules.products.schemas import (
    ProductCreateRequest,
    ProductPaginationResponse,
    ProductResponse,
    ProductUpdateRequest,
)
from app.modules.products.service import (
    create_product,
    delete_product,
    get_product_by_id,
    get_product_by_slug,
    list_products,
    update_product,
)
from app.modules.users.models import User, UserRole

router = APIRouter(prefix="/products", tags=["Products"])


@router.get(
    "",
    response_model=Union[ProductPaginationResponse, List[ProductResponse]],
    summary="List products with composable storefront search, filters, sorting, and pagination",
)
def get_products(
    include_inactive: bool = Query(False, description="Include inactive/draft products (Admin only)"),
    status: Optional[str] = Query(None, description="Filter by product status (Admin only)"),
    category_id: Optional[int] = Query(None, description="Filter by Category ID"),
    category: Optional[str] = Query(None, description="Filter by Category slug or name"),
    brand_id: Optional[int] = Query(None, description="Filter by Brand ID"),
    brand: Optional[str] = Query(None, description="Filter by Brand slug or name"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price filter"),
    search: Optional[str] = Query(None, description="Search product name, SKU, description, brand, category"),
    in_stock: Optional[bool] = Query(None, description="Filter in-stock products only"),
    socket: Optional[str] = Query(None, description="Filter by CPU/Motherboard socket (e.g. AM5, LGA1700)"),
    cores_min: Optional[int] = Query(None, ge=0, description="Minimum CPU core count"),
    threads_min: Optional[int] = Query(None, ge=0, description="Minimum CPU thread count"),
    tdp_max: Optional[int] = Query(None, ge=0, description="Maximum TDP watts"),
    vram_min: Optional[int] = Query(None, ge=0, description="Minimum GPU VRAM in GB"),
    gpu_chipset: Optional[str] = Query(None, description="Filter by GPU chipset"),
    gpu_memory_type: Optional[str] = Query(None, description="Filter by GPU memory type (e.g. GDDR6)"),
    form_factor: Optional[str] = Query(None, description="Filter by Motherboard form factor (e.g. ATX)"),
    memory_type: Optional[str] = Query(None, description="Filter by RAM/Motherboard memory type (e.g. DDR5)"),
    capacity_min: Optional[int] = Query(None, ge=0, description="Minimum RAM/Storage capacity in GB"),
    storage_type: Optional[str] = Query(None, description="Filter by Storage type (e.g. NVMe SSD)"),
    wattage_min: Optional[int] = Query(None, ge=0, description="Minimum PSU wattage"),
    efficiency_rating: Optional[str] = Query(None, description="Filter by PSU efficiency (e.g. 80 Plus Gold)"),
    case_type: Optional[str] = Query(None, description="Filter by Case type (e.g. Mid Tower)"),
    cooler_type: Optional[str] = Query(None, description="Filter by Cooler type (e.g. AIO Liquid Cooler)"),
    sort: Optional[str] = Query("newest", description="Sort order: relevance, price_asc, price_desc, name_asc, name_desc, newest, oldest"),
    page: Optional[int] = Query(None, ge=1, description="Page number for pagination"),
    page_size: Optional[int] = Query(None, ge=1, le=100, description="Items per page"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Storefront catalog search and filtering endpoint:
    - Public listing returns active products with status='ACTIVE' and is_active=True.
    - Authenticated ADMIN users can pass include_inactive=true and status to view draft/archived products.
    - Supports keyword search across product name, SKU, description, category name, and brand name.
    - Supports category & brand filtering by ID or slug.
    - Supports price range filtering with validation.
    - Supports stock availability filtering using Module 5 Inventory quantities.
    - Supports category-aware specification filtering without row duplication.
    - Supports controlled sorting modes (relevance, price_asc, price_desc, name_asc, name_desc, newest, oldest).
    - Supports optional server-side pagination: returns ProductPaginationResponse if page or page_size is specified,
      or List[ProductResponse] if unpaginated.
    """
    if include_inactive or status:
        if not current_user or current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to view inactive or draft products.",
            )

    return list_products(
        db=db,
        include_inactive=include_inactive,
        status_filter=status,
        category_id=category_id,
        category=category,
        brand_id=brand_id,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        search=search,
        in_stock=in_stock,
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
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{identifier}",
    response_model=ProductResponse,
    summary="Get product by ID or slug",
)
def get_product(
    identifier: str,
    include_inactive: bool = Query(False, description="Include inactive/draft product (Admin only)"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves product details. Public users only receive active products.
    Supports either integer ID or string slug identifier.
    """
    if include_inactive:
        if not current_user or current_user.role != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required to view inactive or draft products.",
            )

    # Check if numeric ID
    if identifier.isdigit():
        product = get_product_by_id(db=db, product_id=int(identifier), include_inactive=include_inactive)
    else:
        product = get_product_by_slug(db=db, slug=identifier, include_inactive=include_inactive)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    return product


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product (Admin only)",
)
def add_product(
    product_in: ProductCreateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Creates a new product record. Restricted to ADMIN users.
    Slug is deterministically generated on the backend.
    """
    return create_product(db=db, product_in=product_in)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product (Admin only)",
)
def edit_product(
    product_id: int,
    product_in: ProductUpdateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Updates an existing product record. Restricted to ADMIN users.
    """
    return update_product(
        db=db,
        product_id=product_id,
        product_in=product_in,
    )


@router.delete(
    "/{product_id}",
    response_model=MessageResponse,
    summary="Delete product (Admin only)",
)
def remove_product(
    product_id: int,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Permanently deletes a product record. Restricted to ADMIN users.
    """
    delete_product(db=db, product_id=product_id)
    return MessageResponse(message="Product deleted successfully.")
