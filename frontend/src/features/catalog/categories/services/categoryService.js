import api from '../../../../services/api';

export const categoryService = {
  /**
   * List categories (active for storefront; include_inactive for admin).
   */
  listCategories: async (params = {}) => {
    const response = await api.get('/api/v1/categories', { params });
    return response.data;
  },

  /**
   * Get category by ID.
   */
  getCategory: async (id, params = {}) => {
    const response = await api.get(`/api/v1/categories/${id}`, { params });
    return response.data;
  },

  /**
   * Create a new category (Admin only).
   */
  createCategory: async (categoryData) => {
    const response = await api.post('/api/v1/categories', categoryData);
    return response.data;
  },

  /**
   * Update category details or status (Admin only).
   */
  updateCategory: async (id, categoryData) => {
    const response = await api.patch(`/api/v1/categories/${id}`, categoryData);
    return response.data;
  },

  /**
   * Delete category record (Admin only).
   */
  deleteCategory: async (id) => {
    const response = await api.delete(`/api/v1/categories/${id}`);
    return response.data;
  },
};

export default categoryService;
