import api from '../../../services/api';

export const productSpecificationService = {
  /**
   * Get product technical specifications by product ID.
   */
  getSpecifications: async (productId, params = {}) => {
    const response = await api.get(`/api/v1/products/${productId}/specifications`, { params });
    return response.data;
  },

  /**
   * Create or update product technical specifications (Admin only).
   */
  upsertSpecifications: async (productId, specData) => {
    const response = await api.put(`/api/v1/products/${productId}/specifications`, specData);
    return response.data;
  },

  /**
   * Delete product technical specifications (Admin only).
   */
  deleteSpecifications: async (productId) => {
    const response = await api.delete(`/api/v1/products/${productId}/specifications`);
    return response.data;
  },
};

export default productSpecificationService;
