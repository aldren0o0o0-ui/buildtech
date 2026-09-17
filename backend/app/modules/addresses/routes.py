from typing import List
from app.core import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.addresses.schemas import (
    AddressCreate,
    AddressResponse,
    AddressUpdate,
)
from app.modules.addresses.service import AddressService
from app.modules.auth.dependencies import require_customer
from app.modules.users.models import User

router = APIRouter(prefix="/addresses", tags=["Addresses"])


@router.get(
    "",
    response_model=List[AddressResponse],
    summary="List customer addresses",
)
def list_addresses(
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Returns all shipping addresses owned by the authenticated customer.
    Ordered with the default address first.
    """
    service = AddressService(db)
    return service.list_addresses(current_user.id)


@router.post(
    "",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create shipping address",
)
def create_address(
    payload: AddressCreate,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Creates a new shipping address for the authenticated customer.
    Automatically sets the address as default if it is the customer's first address.
    """
    service = AddressService(db)
    return service.create_address(current_user.id, payload)


@router.get(
    "/{address_id}",
    response_model=AddressResponse,
    summary="Get shipping address by ID",
)
def get_address(
    address_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Retrieves a single address by ID.
    Returns 404 if the address does not exist or is not owned by the customer.
    """
    service = AddressService(db)
    return service.get_address(address_id, current_user.id)


@router.patch(
    "/{address_id}",
    response_model=AddressResponse,
    summary="Update shipping address",
)
def update_address(
    address_id: int,
    payload: AddressUpdate,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Updates an existing shipping address owned by the customer.
    """
    service = AddressService(db)
    return service.update_address(address_id, current_user.id, payload)


@router.delete(
    "/{address_id}",
    summary="Delete shipping address",
)
def delete_address(
    address_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Deletes a shipping address owned by the customer.
    If the deleted address was default, the next remaining address is promoted to default.
    """
    service = AddressService(db)
    service.delete_address(address_id, current_user.id)
    return {"message": "Address deleted successfully"}


@router.post(
    "/{address_id}/default",
    response_model=AddressResponse,
    summary="Set address as default",
)
def set_default_address(
    address_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """
    Sets the specified address as the customer's default shipping address.
    Atomically unsets default on all other addresses belonging to the customer.
    """
    service = AddressService(db)
    return service.set_default_address(address_id, current_user.id)
