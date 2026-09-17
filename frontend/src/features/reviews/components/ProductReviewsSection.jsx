import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import reviewService from '../services/reviewService';
import ReviewSummary from './ReviewSummary';
import ReviewForm from './ReviewForm';
import ReviewList from './ReviewList';
import { useAuth } from '../../../context/AuthContext';

export const ProductReviewsSection = ({ productId, productName: _productName }) => {
  const { user, isAuthenticated } = useAuth();

  const [summary, setSummary] = useState(null);
  const [reviewsData, setReviewsData] = useState({ items: [], total: 0, page: 1, page_size: 10 });
  const [myReviewState, setMyReviewState] = useState({ has_reviewed: false, can_review: false, my_review: null });
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState('newest');
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [isDeletingId, setIsDeletingId] = useState(null);
  const [actionSuccessMessage, setActionSuccessMessage] = useState('');

  // Fetch product summary
  const loadSummary = useCallback(async () => {
    try {
      const sum = await reviewService.getProductReviewSummary(productId);
      setSummary(sum);
    } catch {
      // Non-blocking fallback
    }
  }, [productId]);

  // Fetch reviews list
  const loadReviews = useCallback(async () => {
    setLoading(true);
    try {
      const data = await reviewService.getProductReviews(productId, page, 10, sortBy);
      setReviewsData(data);
    } catch {
      // Non-blocking fallback
    } finally {
      setLoading(false);
    }
  }, [productId, page, sortBy]);

  // Fetch current user review status
  const loadMyReviewStatus = useCallback(async () => {
    if (!isAuthenticated || !user) {
      setMyReviewState({ has_reviewed: false, can_review: false, my_review: null });
      return;
    }
    try {
      const status = await reviewService.getMyReviewForProduct(productId);
      setMyReviewState(status);
    } catch {
      // User may not be logged in or error
    }
  }, [productId, isAuthenticated, user]);

  useEffect(() => {
    if (productId) {
      loadSummary();
      loadReviews();
      loadMyReviewStatus();
    }
  }, [productId, page, sortBy, isAuthenticated, loadSummary, loadReviews, loadMyReviewStatus]);

  const handleToggleForm = () => {
    setFormError('');
    setShowForm((prev) => !prev);
  };

  const handleFormSubmit = async (formData) => {
    setFormSubmitting(true);
    setFormError('');
    setActionSuccessMessage('');
    try {
      if (myReviewState.has_reviewed && myReviewState.my_review) {
        await reviewService.updateReview(myReviewState.my_review.id, formData);
        setActionSuccessMessage('Your review has been updated successfully!');
      } else {
        await reviewService.createReview(productId, formData);
        setActionSuccessMessage('Thank you! Your verified review has been published.');
      }
      setShowForm(false);
      // Reload reviews and status
      await Promise.all([loadSummary(), loadReviews(), loadMyReviewStatus()]);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to submit review. Please check your input and try again.';
      setFormError(msg);
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleDeleteReview = async (reviewId) => {
    if (!window.confirm('Are you sure you want to delete your review?')) {
      return;
    }
    setIsDeletingId(reviewId);
    try {
      await reviewService.deleteReview(reviewId);
      setActionSuccessMessage('Your review has been deleted.');
      setShowForm(false);
      await Promise.all([loadSummary(), loadReviews(), loadMyReviewStatus()]);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete review.');
    } finally {
      setIsDeletingId(null);
    }
  };

  return (
    <section
      className="product-detail-reviews-section"
      id="customer-reviews"
      aria-labelledby="reviews-heading"
      style={{ marginTop: 'var(--space-10)' }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          marginBottom: 'var(--space-6)',
          borderBottom: '2px solid var(--color-border-subtle, rgba(255, 255, 255, 0.08))',
          paddingBottom: 'var(--space-3)'
        }}
      >
        <h2 id="reviews-heading" className="detail-section-title" style={{ margin: 0 }}>
          Customer Reviews & Ratings
        </h2>
        {summary && (
          <span style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary, #9ca3af)' }}>
            ★ {Number(summary.average_rating).toFixed(1)} / 5 ({summary.total_reviews} reviews)
          </span>
        )}
      </div>

      {actionSuccessMessage && (
        <div
          className="alert alert-success"
          style={{
            padding: 'var(--space-3) var(--space-4)',
            marginBottom: 'var(--space-4)',
            borderRadius: '6px',
            background: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#10b981',
            fontSize: '0.875rem'
          }}
        >
          {actionSuccessMessage}
        </div>
      )}

      {/* Aggregate Review Summary Card */}
      <ReviewSummary
        summary={summary}
        canReview={myReviewState.can_review}
        hasReviewed={myReviewState.has_reviewed}
        isAuthenticated={isAuthenticated}
        onWriteReviewClick={
          !isAuthenticated
            ? null
            : user?.role === 'ADMIN'
            ? null
            : myReviewState.can_review || myReviewState.has_reviewed
            ? handleToggleForm
            : null
        }
      />

      {/* Customer Verification Status Banner if ineligible */}
      {!isAuthenticated && (
        <div
          className="card"
          style={{
            padding: 'var(--space-4)',
            marginBottom: 'var(--space-6)',
            background: 'rgba(99, 102, 241, 0.05)',
            border: '1px dashed var(--color-primary-subtle, rgba(99, 102, 241, 0.3))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 'var(--space-2)'
          }}
        >
          <span style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary, #9ca3af)' }}>
            Have you purchased this item? <strong style={{ color: 'var(--color-text-primary, #f3f4f6)' }}>Sign in</strong> to check your review eligibility.
          </span>
          <Link to="/login" className="btn btn-outline btn-sm">
            Sign In to Review
          </Link>
        </div>
      )}

      {isAuthenticated && user?.role === 'ADMIN' && (
        <div
          className="card"
          style={{
            padding: 'var(--space-3) var(--space-4)',
            marginBottom: 'var(--space-6)',
            background: 'var(--color-surface-muted)',
            border: '1px solid var(--color-border-subtle)',
            fontSize: '0.85rem',
            color: 'var(--color-text-secondary)'
          }}
        >
          <em>You are logged in as an Administrator. Reviews can be moderated in the Admin Portal.</em>
        </div>
      )}

      {isAuthenticated && user?.role !== 'ADMIN' && !myReviewState.can_review && !myReviewState.has_reviewed && (
        <div
          className="card"
          style={{
            padding: 'var(--space-4)',
            marginBottom: 'var(--space-6)',
            background: 'var(--color-surface-muted)',
            border: '1px solid var(--color-border-subtle)',
            fontSize: '0.875rem',
            color: 'var(--color-text-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)'
          }}
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0, color: 'var(--color-text-secondary)' }}>
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          <div>
            <strong style={{ color: 'var(--color-text)' }}>Verified Purchaser Reviews:</strong>{' '}
            Only customers who have purchased this product in a confirmed order can submit a review.
          </div>
        </div>
      )}

      {/* Review Form (when open) */}
      {showForm && (
        <ReviewForm
          initialReview={myReviewState.my_review}
          onSubmit={handleFormSubmit}
          onCancel={handleToggleForm}
          isSubmitting={formSubmitting}
          error={formError}
        />
      )}

      {/* Reviews List */}
      <ReviewList
        reviews={reviewsData.items}
        total={reviewsData.total}
        page={reviewsData.page}
        pageSize={reviewsData.page_size}
        sortBy={sortBy}
        onSortChange={(sort) => {
          setSortBy(sort);
          setPage(1);
        }}
        onPageChange={(newPage) => setPage(newPage)}
        currentUserId={user?.id}
        onEditReview={() => setShowForm(true)}
        onDeleteReview={handleDeleteReview}
        isDeletingId={isDeletingId}
        loading={loading}
      />
    </section>
  );
};

export default ProductReviewsSection;
