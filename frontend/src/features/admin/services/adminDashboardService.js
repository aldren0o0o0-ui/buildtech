import api from '../../../services/api';

export const adminDashboardService = {
  /**
   * Fetches authoritative operational dashboard data:
   * overview metrics, order status counts, low-stock warnings, top sellers, and recent orders.
   */
  async getDashboardData() {
    const response = await api.get('/api/v1/admin/dashboard');
    return response.data;
  },
};

export default adminDashboardService;
