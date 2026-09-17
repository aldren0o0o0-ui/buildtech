from typing import List, Optional
from sqlalchemy.orm import Session

from app.modules.addresses.models import Address


class AddressRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_user_id(self, user_id: int) -> List[Address]:
        """Returns all addresses for a customer, with default address first, followed by newest."""
        return (
            self.db.query(Address)
            .filter(Address.user_id == user_id)
            .order_by(Address.is_default.desc(), Address.created_at.desc())
            .all()
        )

    def get_by_id(self, address_id: int, user_id: int) -> Optional[Address]:
        """Returns a customer-scoped address by ID, ensuring strict tenant isolation."""
        return (
            self.db.query(Address)
            .filter(Address.id == address_id, Address.user_id == user_id)
            .first()
        )

    def get_default(self, user_id: int) -> Optional[Address]:
        """Returns the customer's current default address if one is set."""
        return (
            self.db.query(Address)
            .filter(Address.user_id == user_id, Address.is_default.is_(True))
            .first()
        )

    def count_by_user_id(self, user_id: int) -> int:
        """Returns total count of saved addresses for a customer."""
        return self.db.query(Address).filter(Address.user_id == user_id).count()

    def create(self, address: Address) -> Address:
        """Persists a new address."""
        self.db.add(address)
        self.db.commit()
        self.db.refresh(address)
        return address

    def update(self, address: Address) -> Address:
        """Commits modifications to an existing address."""
        self.db.commit()
        self.db.refresh(address)
        return address

    def delete(self, address: Address) -> None:
        """Removes an address from the database."""
        self.db.delete(address)
        self.db.commit()

    def clear_default(self, user_id: int, exclude_id: Optional[int] = None) -> None:
        """
        Unsets is_default for all addresses belonging to the customer,
        optionally excluding a specific address ID.
        """
        query = self.db.query(Address).filter(
            Address.user_id == user_id,
            Address.is_default.is_(True),
        )
        if exclude_id is not None:
            query = query.filter(Address.id != exclude_id)
        query.update({"is_default": False}, synchronize_session="fetch")
        self.db.flush()
