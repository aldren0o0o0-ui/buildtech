import api from '../../../services/api';

export const checkoutService = {
  /**
   * Performs non-destructive checkout validation against current cart and selected address.
   * Re-evaluates active status, live inventory, and authoritative price totals.
   */
  validateCheckout: async (addressId) => {
    const response = await api.post('/api/v1/checkout/validate', {
      address_id: addressId,
    });
    return response.data;
  },
};

export default checkoutService;
