import api from '../../../../services/api';

export const brandService = {
  /**
   * List brands (active for storefront; include_inactive for admin).
   */
  listBrands: async (params = {}) => {
    const response = await api.get('/api/v1/brands', { params });
    return response.data;
  },

  /**
   * Get brand by ID.
   */
  getBrand: async (id, params = {}) => {
    const response = await api.get(`/api/v1/brands/${id}`, { params });
    return response.data;
  },

  /**
   * Create a new brand (Admin only).
   */
  createBrand: async (brandData) => {
    const response = await api.post('/api/v1/brands', brandData);
    return response.data;
  },

  /**
   * Update brand details or status (Admin only).
   */
  updateBrand: async (id, brandData) => {
    const response = await api.patch(`/api/v1/brands/${id}`, brandData);
    return response.data;
  },

  /**
   * Delete brand record (Admin only).
   */
  deleteBrand: async (id) => {
    const response = await api.delete(`/api/v1/brands/${id}`);
    return response.data;
  },
};

export default brandService;
