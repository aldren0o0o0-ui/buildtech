"""
Compatibility Engine Repository (Module 14).

Performs lightweight, pure read-only loading of authoritative product specifications
from PostgreSQL using eager joined loading to prevent N+1 query overhead.
"""

from typing import List, Tuple
from app.core import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.modules.products.models import Product, ProductStatus


class CompatibilityRepository:
    """Read-only data access layer for hardware products and specifications."""

    def __init__(self, db: Session):
        self.db = db

    def get_products_by_ids(
        self,
        product_ids: List[int],
        require_active: bool = True,
    ) -> List[Product]:
        """
        Loads products and all associated technical specifications in a single batch query.
        Validates that all requested IDs exist in PostgreSQL.
        """
        if not product_ids:
            return []

        # Deduplicate while preserving order
        unique_ids = list(dict.fromkeys(product_ids))

        query = (
            self.db.query(Product)
            .options(
                joinedload(Product.cpu_spec),
                joinedload(Product.gpu_spec),
                joinedload(Product.motherboard_spec),
                joinedload(Product.memory_spec),
                joinedload(Product.storage_spec),
                joinedload(Product.psu_spec),
                joinedload(Product.case_spec),
                joinedload(Product.cooling_spec),
                joinedload(Product.category),
                joinedload(Product.brand),
            )
            .filter(Product.id.in_(unique_ids))
        )

        if require_active:
            query = query.filter(
                Product.is_active.is_(True),
                Product.status == ProductStatus.ACTIVE.value,
            )

        products = query.all()

        # Check for missing products
        found_ids = {p.id for p in products}
        missing_ids = [pid for pid in unique_ids if pid not in found_ids]

        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"The following product IDs were not found or are inactive: {missing_ids}",
            )

        # Return products in the order requested by client
        product_map = {p.id: p for p in products}
        return [product_map[pid] for pid in unique_ids]
