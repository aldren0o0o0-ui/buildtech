import api from '../../../services/api';

export const paymentService = {
  /**
   * Get payment details for an order owned by current customer.
   * Scoped to /api/v1/orders/{orderIdentifier}/payment.
   */
  async getOrderPayment(orderIdentifier) {
    const response = await api.get(`/api/v1/orders/${orderIdentifier}/payment`);
    return response.data;
  },

  /**
   * List payments for administration with filtering, search, and pagination.
   */
  async getAdminPayments(params = {}) {
    const response = await api.get('/api/v1/admin/payments', { params });
    return response.data;
  },

  /**
   * Get administrative payment record by ID.
   */
  async getAdminPaymentDetail(paymentId) {
    const response = await api.get(`/api/v1/admin/payments/${paymentId}`);
    return response.data;
  },

  /**
   * Mark a Cash on Delivery payment as collected/paid.
   * Admin only action.
   */
  async markCodPaymentPaid(paymentId) {
    const response = await api.post(`/api/v1/admin/payments/${paymentId}/mark-paid`);
    return response.data;
  },

  /**
   * Update payment status via state machine.
   * Admin only action.
   */
  async updateAdminPaymentStatus(paymentId, status, notes = null) {
    const response = await api.patch(`/api/v1/admin/payments/${paymentId}/status`, {
      status,
      notes,
    });
    return response.data;
  },
};

export default paymentService;
