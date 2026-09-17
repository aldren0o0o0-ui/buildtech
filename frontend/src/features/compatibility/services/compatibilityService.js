import api from '../../../services/api';

export const compatibilityService = {
  /**
   * Check compatibility for a list of product IDs.
   * @param {number[]} productIds - Authoritative product IDs to check.
   * @returns {Promise<Object>} CompatibilityResponse
   */
  checkCompatibility: async (productIds) => {
    const response = await api.post('/api/v1/compatibility/check', {
      product_ids: productIds,
    });
    return response.data;
  },
};

export default compatibilityService;
