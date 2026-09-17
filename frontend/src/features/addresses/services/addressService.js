import api from '../../../services/api';

export const addressService = {
  /**
   * Retrieves all saved shipping addresses for the customer.
   */
  getAddresses: async () => {
    const response = await api.get('/api/v1/addresses');
    return response.data;
  },

  /**
   * Retrieves a single address by ID.
   */
  getAddress: async (id) => {
    const response = await api.get(`/api/v1/addresses/${id}`);
    return response.data;
  },

  /**
   * Creates a new shipping address.
   */
  createAddress: async (data) => {
    const response = await api.post('/api/v1/addresses', data);
    return response.data;
  },

  /**
   * Updates an existing shipping address.
   */
  updateAddress: async (id, data) => {
    const response = await api.patch(`/api/v1/addresses/${id}`, data);
    return response.data;
  },

  /**
   * Deletes a shipping address.
   */
  deleteAddress: async (id) => {
    const response = await api.delete(`/api/v1/addresses/${id}`);
    return response.data;
  },

  /**
   * Sets the specified address as default.
   */
  setDefaultAddress: async (id) => {
    const response = await api.post(`/api/v1/addresses/${id}/default`);
    return response.data;
  },
};

export default addressService;
