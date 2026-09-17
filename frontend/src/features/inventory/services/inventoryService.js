import api from '../../../services/api';

export const inventoryService = {
  /**
   * List all product inventories with optional search and availability filter (Admin only).
   */
  listInventory: async (params = {}) => {
    const response = await api.get('/api/v1/inventory', { params });
    return response.data;
  },

  /**
   * Get inventory details for a product (Admin only).
   */
  getInventory: async (productId) => {
    const response = await api.get(`/api/v1/inventory/${productId}`);
    return response.data;
  },

  /**
   * Receive new physical stock (Admin only).
   */
  stockIn: async (productId, data) => {
    const response = await api.post(`/api/v1/inventory/${productId}/stock-in`, data);
    return response.data;
  },

  /**
   * Adjust inventory upward or downward (Admin only).
   */
  adjustInventory: async (productId, data) => {
    const response = await api.post(`/api/v1/inventory/${productId}/adjust`, data);
    return response.data;
  },

  /**
   * Update low stock threshold alert level (Admin only).
   */
  updateThreshold: async (productId, data) => {
    const response = await api.patch(`/api/v1/inventory/${productId}/threshold`, data);
    return response.data;
  },

  /**
   * Get immutable transaction audit trail (Admin only).
   */
  getTransactions: async (productId) => {
    const response = await api.get(`/api/v1/inventory/${productId}/transactions`);
    return response.data;
  },

  /**
   * Get public product availability indicator.
   */
  getProductAvailability: async (productId) => {
    const response = await api.get(`/api/v1/products/${productId}/availability`);
    return response.data;
  },
};

export default inventoryService;
