import api from '../../../services/api';

export const orderService = {
  /**
   * Submit authoritative Module 10 order creation request.
   * Supports saved address_id, notes, and optional idempotency key.
   */
  async createOrder(orderData, idempotencyKey = null) {
    const headers = {};
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }
    const response = await api.post('/api/v1/orders', orderData, { headers });
    return response.data;
  },

  /**
   * Submit checkout request to convert customer's cart to an immutable order.
   * Supports optional idempotency key for network retry safety.
   */
  async checkout(checkoutData, idempotencyKey = null) {
    const headers = {};
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }
    const response = await api.post('/api/v1/checkout', checkoutData, { headers });
    return response.data;
  },

  /**
   * List orders placed by authenticated customer with optional pagination and status filter.
   */
  async getMyOrders(page = 1, pageSize = 10, status = null) {
    const params = { page, page_size: pageSize };
    if (status) {
      params.status = status;
    }
    const response = await api.get('/api/v1/orders', { params });
    return response.data;
  },

  /**
   * Get full details of an order owned by current customer.
   * Accepts numeric ID or alphanumeric order number.
   */
  async getMyOrderDetail(orderIdentifier) {
    const response = await api.get(`/api/v1/orders/${orderIdentifier}`);
    return response.data;
  },

  /**
   * Cancel an eligible order as a customer.
   */
  async cancelMyOrder(orderIdentifier) {
    const response = await api.post(`/api/v1/orders/${orderIdentifier}/cancel`);
    return response.data;
  },

  /**
   * List all customer orders for administration with search and filtering.
   */
  async getAdminOrders(params = {}) {
    const response = await api.get('/api/v1/admin/orders', { params });
    return response.data;
  },

  /**
   * Get administrative order details by integer ID.
   */
  async getAdminOrderDetail(orderId) {
    const response = await api.get(`/api/v1/admin/orders/${orderId}`);
    return response.data;
  },

  /**
   * Update order status following strict business state transitions.
   */
  async updateAdminOrderStatus(orderId, targetStatus) {
    const response = await api.patch(`/api/v1/admin/orders/${orderId}/status`, {
      status: targetStatus,
    });
    return response.data;
  },

  /**
   * Admin order cancellation with inventory recovery.
   */
  async cancelAdminOrder(orderId) {
    const response = await api.post(`/api/v1/admin/orders/${orderId}/cancel`);
    return response.data;
  },
};

export default orderService;
