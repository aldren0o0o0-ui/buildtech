import api from '../../../services/api';

export const cartService = {
  /**
   * Retrieves the authenticated customer's current shopping cart.
   */
  getCart: async () => {
    const response = await api.get('/api/v1/cart');
    return response.data;
  },

  /**
   * Adds an active product to the customer's cart.
   */
  addToCart: async (productId, quantity = 1) => {
    const response = await api.post('/api/v1/cart/items', {
      product_id: productId,
      quantity,
    });
    return response.data;
  },

  /**
   * Updates the quantity of a specific cart item.
   */
  updateCartItem: async (itemId, quantity) => {
    const response = await api.patch(`/api/v1/cart/items/${itemId}`, {
      quantity,
    });
    return response.data;
  },

  /**
   * Removes a specific item from the cart.
   */
  removeCartItem: async (itemId) => {
    const response = await api.delete(`/api/v1/cart/items/${itemId}`);
    return response.data;
  },

  /**
   * Clears all items from the customer's cart.
   */
  clearCart: async () => {
    const response = await api.delete('/api/v1/cart');
    return response.data;
  },
};

export default cartService;
