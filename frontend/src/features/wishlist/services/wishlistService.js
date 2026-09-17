import api from '../../../services/api';

export const wishlistService = {
  /**
   * Retrieves the authenticated customer's wishlist with live availability.
   */
  getWishlist: async () => {
    const response = await api.get('/api/v1/wishlist');
    return response.data;
  },

  /**
   * Adds an active product to the customer's wishlist.
   */
  addToWishlist: async (productId) => {
    const response = await api.post('/api/v1/wishlist/items', {
      product_id: productId,
    });
    return response.data;
  },

  /**
   * Removes an item from the customer's wishlist by item ID.
   */
  removeFromWishlist: async (itemId) => {
    const response = await api.delete(`/api/v1/wishlist/items/${itemId}`);
    return response.data;
  },

  /**
   * Lightweight existence check for a specific product ID.
   */
  checkWishlistStatus: async (productId) => {
    const response = await api.get(`/api/v1/wishlist/check/${productId}`);
    return response.data;
  },
};

export default wishlistService;
