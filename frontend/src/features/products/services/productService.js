import api from '../../../services/api';

export const productService = {
  /**
   * List products (public active only by default; all if include_inactive=true for admin).
   */
  listProducts: async (params = {}) => {
    const response = await api.get('/api/v1/products', { params });
    return response.data;
  },

  /**
   * Get product by ID or slug.
   */
  getProduct: async (identifier, params = {}) => {
    const response = await api.get(`/api/v1/products/${identifier}`, { params });
    return response.data;
  },

  /**
   * Create a new product (Admin only).
   */
  createProduct: async (productData) => {
    const response = await api.post('/api/v1/products', productData);
    return response.data;
  },

  /**
   * Update product details or status (Admin only).
   */
  updateProduct: async (id, productData) => {
    const response = await api.patch(`/api/v1/products/${id}`, productData);
    return response.data;
  },

  /**
   * Delete product record (Admin only).
   */
  deleteProduct: async (id) => {
    const response = await api.delete(`/api/v1/products/${id}`);
    return response.data;
  },
};

export default productService;
