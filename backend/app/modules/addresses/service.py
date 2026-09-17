from typing import List
from app.core import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.addresses.models import Address
from app.modules.addresses.repository import AddressRepository
from app.modules.addresses.schemas import AddressCreate, AddressUpdate


class AddressService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AddressRepository(db)

    def list_addresses(self, user_id: int) -> List[Address]:
        """Lists all shipping addresses owned by the authenticated customer."""
        return self.repo.list_by_user_id(user_id)

    def get_address(self, address_id: int, user_id: int) -> Address:
        """
        Retrieves a single address owned by the customer.
        Returns 404 if the address does not exist or belongs to another user.
        """
        address = self.repo.get_by_id(address_id, user_id)
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found",
            )
        return address

    def create_address(self, user_id: int, data: AddressCreate) -> Address:
        """
        Creates a new shipping address.
        - If this is the customer's first address, it automatically becomes the default.
        - If is_default is True, existing default addresses for this customer are atomically unset.
        """
        existing_count = self.repo.count_by_user_id(user_id)
        should_be_default = data.is_default or (existing_count == 0)

        if should_be_default:
            self.repo.clear_default(user_id)

        address = Address(
            user_id=user_id,
            label=data.label,
            recipient_name=data.recipient_name,
            phone=data.phone,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            barangay=data.barangay,
            city=data.city,
            province=data.province,
            postal_code=data.postal_code,
            country=data.country,
            is_default=should_be_default,
        )
        return self.repo.create(address)

    def update_address(
        self,
        address_id: int,
        user_id: int,
        data: AddressUpdate,
    ) -> Address:
        """
        Updates an existing shipping address.
        Enforces customer isolation and atomic default address guarantees.
        """
        address = self.get_address(address_id, user_id)

        update_dict = data.model_dump(exclude_unset=True)

        # Handle is_default transition
        if update_dict.get("is_default") is True:
            self.repo.clear_default(user_id, exclude_id=address_id)

        for field, value in update_dict.items():
            setattr(address, field, value)

        return self.repo.update(address)

    def delete_address(self, address_id: int, user_id: int) -> None:
        """
        Deletes a shipping address.
        If the deleted address was the default address, automatically promotes the
        most recent remaining address to become the new default.
        """
        address = self.get_address(address_id, user_id)
        was_default = address.is_default

        self.repo.delete(address)

        if was_default:
            # Promote next remaining address if any exists
            remaining = self.repo.list_by_user_id(user_id)
            if remaining:
                remaining[0].is_default = True
                self.repo.update(remaining[0])

    def set_default_address(self, address_id: int, user_id: int) -> Address:
        """
        Explicitly sets an existing address as the customer's default address.
        Atomically unsets default on all other addresses belonging to the customer.
        """
        address = self.get_address(address_id, user_id)
        if not address.is_default:
            self.repo.clear_default(user_id, exclude_id=address_id)
            address.is_default = True
            return self.repo.update(address)
        return address
