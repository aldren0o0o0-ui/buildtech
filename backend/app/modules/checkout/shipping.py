from decimal import Decimal
from app.modules.addresses.models import Address


class ShippingService:
    """
    Centralized service for computing authoritative shipping fees.
    Decoupled from checkout validation to allow easy evolution in future logistics modules.
    """

    @staticmethod
    def calculate_shipping_fee(subtotal: Decimal, address: Address) -> Decimal:
        """
        Determines the shipping fee based on subtotal and destination address.
        Default BuildTech baseline provides free standard shipping (0.00).
        """
        return Decimal("0.00")
