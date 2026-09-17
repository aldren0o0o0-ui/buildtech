import api from '../../../services/api';

export const reviewService = {
  /**
   * Get paginated public reviews for a product (PUBLISHED only).
   */
  async getProductReviews(productId, page = 1, pageSize = 10, sortBy = 'newest') {
    const params = { page, page_size: pageSize, sort_by: sortBy };
    const response = await api.get(`/api/v1/products/${productId}/reviews`, { params });
    return response.data;
  },

  /**
   * Get rating summary and distribution for a product.
   */
  async getProductReviewSummary(productId) {
    const response = await api.get(`/api/v1/products/${productId}/reviews/summary`);
    return response.data;
  },

  /**
   * Check if current authenticated customer has reviewed this product and whether they are eligible.
   */
  async getMyReviewForProduct(productId) {
    const response = await api.get(`/api/v1/reviews/products/${productId}/my-review`);
    return response.data;
  },

  /**
   * Submit a verified customer review for a product.
   */
  async createReview(productId, reviewData) {
    const response = await api.post(`/api/v1/products/${productId}/reviews`, reviewData);
    return response.data;
  },

  /**
   * Edit customer's existing review.
   */
  async updateReview(reviewId, reviewData) {
    const response = await api.put(`/api/v1/reviews/${reviewId}`, reviewData);
    return response.data;
  },

  /**
   * Delete customer's own review.
   */
  async deleteReview(reviewId) {
    const response = await api.delete(`/api/v1/reviews/${reviewId}`);
    return response.data;
  },

  /**
   * Admin list of all reviews across products with filters.
   */
  async adminListReviews(page = 1, pageSize = 20, status = null, search = null, productId = null) {
    const params = { page, page_size: pageSize };
    if (status) params.status = status;
    if (search) params.search = search;
    if (productId) params.product_id = productId;
    const response = await api.get('/api/v1/admin/reviews', { params });
    return response.data;
  },

  /**
   * Admin moderation: publish or hide a review.
   */
  async adminUpdateStatus(reviewId, status) {
    const response = await api.patch(`/api/v1/admin/reviews/${reviewId}/status`, { status });
    return response.data;
  },

  /**
   * Admin permanently delete a review.
   */
  async adminDeleteReview(reviewId) {
    const response = await api.delete(`/api/v1/admin/reviews/${reviewId}`);
    return response.data;
  }
};

export default reviewService;
