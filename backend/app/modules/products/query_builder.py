from decimal import Decimal
import math
from typing import Any, Dict, List, Optional, Tuple, Union
from app.core import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Query, Session, joinedload

from app.modules.catalog.brand_model import Brand
from app.modules.catalog.category_model import Category
from app.modules.inventory.models import Inventory
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

VALID_SORT_MODES = {
    "relevance",
    "price_asc",
    "price_desc",
    "name_asc",
    "name_desc",
    "newest",
    "oldest",
}


class ProductQueryBuilder:
    """
    Composable Query Builder for Storefront Product Search, Filtering, Sorting, and Pagination.
    Uses SQLAlchemy EXISTS subqueries for specifications to guarantee one-product-one-result
    and prevent row duplication.
    """

    def __init__(
        self,
        db: Session,
        include_inactive: bool = False,
        status_filter: Optional[str] = None,
    ):
        self.db = db
        self.include_inactive = include_inactive
        self.status_filter = status_filter
        self.search_term_clean: Optional[str] = None

        # Base query with eager-loaded relationships to avoid N+1 queries
        self.query: Query = (
            self.db.query(Product)
            .options(
                joinedload(Product.category),
                joinedload(Product.brand),
                joinedload(Product.inventory),
            )
        )

        # Apply visibility constraints
        if not self.include_inactive:
            self.query = self.query.filter(
                Product.is_active.is_(True),
                Product.status == ProductStatus.ACTIVE.value,
            )
        elif self.status_filter:
            self.query = self.query.filter(
                Product.status == self.status_filter.strip().upper()
            )

    def apply_search(self, search: Optional[str]) -> "ProductQueryBuilder":
        """Search across product name, sku, description, brand name, and category name."""
        if not search or not search.strip():
            return self

        clean = search.strip()
        self.search_term_clean = clean
        term = f"%{clean}%"

        self.query = self.query.filter(
            or_(
                Product.name.ilike(term),
                Product.sku.ilike(term),
                Product.description.ilike(term),
                Product.brand.has(Brand.name.ilike(term)),
                Product.category.has(Category.name.ilike(term)),
            )
        )
        return self

    def apply_category(
        self,
        category_id: Optional[int] = None,
        category_slug: Optional[str] = None,
    ) -> "ProductQueryBuilder":
        """Filter by Category ID or slug."""
        if category_id is not None:
            self.query = self.query.filter(Product.category_id == category_id)
        elif category_slug and category_slug.strip():
            slug = category_slug.strip()
            self.query = self.query.filter(
                Product.category.has(
                    or_(Category.slug.ilike(slug), Category.name.ilike(slug))
                )
            )
        return self

    def apply_brand(
        self,
        brand_id: Optional[int] = None,
        brand_slug: Optional[str] = None,
    ) -> "ProductQueryBuilder":
        """Filter by Brand ID or slug."""
        if brand_id is not None:
            self.query = self.query.filter(Product.brand_id == brand_id)
        elif brand_slug and brand_slug.strip():
            slug = brand_slug.strip()
            self.query = self.query.filter(
                Product.brand.has(
                    or_(Brand.slug.ilike(slug), Brand.name.ilike(slug))
                )
            )
        return self

    def apply_price_range(
        self,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
    ) -> "ProductQueryBuilder":
        """Filter by monetary price range with validation."""
        if min_price is not None and min_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum price cannot be negative.",
            )
        if max_price is not None and max_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum price cannot be negative.",
            )
        if (
            min_price is not None
            and max_price is not None
            and min_price > max_price
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum price cannot exceed maximum price.",
            )

        if min_price is not None:
            self.query = self.query.filter(Product.price >= min_price)
        if max_price is not None:
            self.query = self.query.filter(Product.price <= max_price)
        return self

    def apply_availability(self, in_stock: Optional[bool]) -> "ProductQueryBuilder":
        """Filter by stock availability using Module 5 Inventory quantities."""
        if in_stock is True:
            self.query = self.query.filter(
                Product.inventory.has(
                    Inventory.quantity > Inventory.reserved_quantity
                )
            )
        elif in_stock is False:
            self.query = self.query.filter(
                or_(
                    ~Product.inventory.has(),
                    Product.inventory.has(
                        Inventory.quantity <= Inventory.reserved_quantity
                    ),
                )
            )
        return self

    def apply_specifications(
        self,
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
    ) -> "ProductQueryBuilder":
        """
        Category-aware specification filters using EXISTS subqueries.
        Guarantees zero duplicate product rows across multiple criteria.
        """
        # CPU & Motherboard socket
        if socket and socket.strip():
            s = socket.strip()
            self.query = self.query.filter(
                or_(
                    Product.cpu_spec.has(CpuSpecification.socket.ilike(s)),
                    Product.motherboard_spec.has(MotherboardSpecification.socket.ilike(s)),
                )
            )

        # CPU core count
        if cores_min is not None:
            if cores_min < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="cores_min must be a non-negative integer.",
                )
            self.query = self.query.filter(
                Product.cpu_spec.has(CpuSpecification.core_count >= cores_min)
            )

        # CPU thread count
        if threads_min is not None:
            if threads_min < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="threads_min must be a non-negative integer.",
                )
            self.query = self.query.filter(
                Product.cpu_spec.has(CpuSpecification.thread_count >= threads_min)
            )

        # TDP max (CPU or GPU)
        if tdp_max is not None:
            if tdp_max < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="tdp_max must be a non-negative integer.",
                )
            self.query = self.query.filter(
                or_(
                    Product.cpu_spec.has(CpuSpecification.tdp_watts <= tdp_max),
                    Product.gpu_spec.has(GpuSpecification.tdp_watts <= tdp_max),
                )
            )

        # GPU VRAM
        if vram_min is not None:
            if vram_min < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="vram_min must be a non-negative integer.",
                )
            self.query = self.query.filter(
                Product.gpu_spec.has(GpuSpecification.vram_gb >= vram_min)
            )

        # GPU Chipset
        if gpu_chipset and gpu_chipset.strip():
            chip = f"%{gpu_chipset.strip()}%"
            self.query = self.query.filter(
                Product.gpu_spec.has(GpuSpecification.chipset.ilike(chip))
            )

        # GPU Memory Type
        if gpu_memory_type and gpu_memory_type.strip():
            gmt = gpu_memory_type.strip()
            self.query = self.query.filter(
                Product.gpu_spec.has(GpuSpecification.memory_type.ilike(gmt))
            )

        # Motherboard Form Factor
        if form_factor and form_factor.strip():
            ff = form_factor.strip()
            self.query = self.query.filter(
                Product.motherboard_spec.has(MotherboardSpecification.form_factor.ilike(ff))
            )

        # RAM / Motherboard Memory Type (DDR4, DDR5)
        if memory_type and memory_type.strip():
            mt = memory_type.strip()
            self.query = self.query.filter(
                or_(
                    Product.memory_spec.has(MemorySpecification.memory_type.ilike(mt)),
                    Product.motherboard_spec.has(MotherboardSpecification.memory_type.ilike(mt)),
                )
            )

        # RAM / Storage Capacity min
        if capacity_min is not None:
            if capacity_min < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="capacity_min must be a non-negative integer.",
                )
            self.query = self.query.filter(
                or_(
                    Product.memory_spec.has(MemorySpecification.capacity_gb >= capacity_min),
                    Product.storage_spec.has(StorageSpecification.capacity_gb >= capacity_min),
                )
            )

        # Storage Type (NVMe SSD, SATA SSD, HDD)
        if storage_type and storage_type.strip():
            st = f"%{storage_type.strip()}%"
            self.query = self.query.filter(
                Product.storage_spec.has(StorageSpecification.storage_type.ilike(st))
            )

        # PSU Wattage min
        if wattage_min is not None:
            if wattage_min < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="wattage_min must be a non-negative integer.",
                )
            self.query = self.query.filter(
                Product.psu_spec.has(PsuSpecification.wattage >= wattage_min)
            )

        # PSU Efficiency Rating (80 Plus Gold, Platinum, etc.)
        if efficiency_rating and efficiency_rating.strip():
            eff = f"%{efficiency_rating.strip()}%"
            self.query = self.query.filter(
                Product.psu_spec.has(PsuSpecification.efficiency_rating.ilike(eff))
            )

        # Case Type (Mid Tower, Full Tower, Mini-ITX)
        if case_type and case_type.strip():
            ct = f"%{case_type.strip()}%"
            self.query = self.query.filter(
                Product.case_spec.has(CaseSpecification.case_type.ilike(ct))
            )

        # Cooler Type (AIO Liquid, Air Cooler)
        if cooler_type and cooler_type.strip():
            cl = f"%{cooler_type.strip()}%"
            self.query = self.query.filter(
                Product.cooling_spec.has(CoolingSpecification.cooler_type.ilike(cl))
            )

        return self

    def apply_sorting(self, sort: Optional[str]) -> "ProductQueryBuilder":
        """Apply controlled sort mapping."""
        if not sort:
            sort = "newest"

        clean_sort = sort.strip().lower()
        if clean_sort not in VALID_SORT_MODES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid sort option '{sort}'. "
                    f"Supported options: {', '.join(sorted(list(VALID_SORT_MODES)))}."
                ),
            )

        if clean_sort == "price_asc":
            self.query = self.query.order_by(Product.price.asc(), Product.id.asc())
        elif clean_sort == "price_desc":
            self.query = self.query.order_by(Product.price.desc(), Product.id.desc())
        elif clean_sort == "name_asc":
            self.query = self.query.order_by(Product.name.asc(), Product.id.asc())
        elif clean_sort == "name_desc":
            self.query = self.query.order_by(Product.name.desc(), Product.id.desc())
        elif clean_sort == "oldest":
            self.query = self.query.order_by(Product.created_at.asc(), Product.id.asc())
        elif clean_sort == "relevance":
            if self.search_term_clean:
                # Rank exact prefix starts-with matches higher, then alphabetical
                prefix = f"{self.search_term_clean}%"
                self.query = self.query.order_by(
                    Product.name.ilike(prefix).desc(),
                    Product.name.asc(),
                )
            else:
                self.query = self.query.order_by(Product.created_at.desc(), Product.id.desc())
        else:
            # Default: newest arrivals first
            self.query = self.query.order_by(Product.created_at.desc(), Product.id.desc())

        return self

    def execute(
        self,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Union[List[Product], Dict[str, Any]]:
        """
        Executes the built query.
        - If page or page_size is provided, returns paginated dict envelope:
          { items, total, page, page_size, total_pages, pages }
        - If neither is provided, returns List[Product] for backward compatibility.
        """
        if page is not None or page_size is not None:
            effective_page = page if page is not None else 1
            effective_size = page_size if page_size is not None else 12

            if effective_page < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Page number must be an integer greater than or equal to 1.",
                )
            if effective_size < 1 or effective_size > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Page size must be between 1 and 100.",
                )

            total = self.query.count()
            total_pages = math.ceil(total / effective_size) if total > 0 else 1

            items = (
                self.query.offset((effective_page - 1) * effective_size)
                .limit(effective_size)
                .all()
            )

            return {
                "items": items,
                "total": total,
                "page": effective_page,
                "page_size": effective_size,
                "total_pages": total_pages,
                "pages": total_pages,
            }

        return self.query.all()
