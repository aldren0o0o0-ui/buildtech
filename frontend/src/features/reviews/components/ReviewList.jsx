import React from 'react';
import ReviewCard from './ReviewCard';

export const ReviewList = ({
  reviews = [],
  total = 0,
  page = 1,
  pageSize = 10,
  sortBy = 'newest',
  onSortChange,
  onPageChange,
  currentUserId = null,
  onEditReview = null,
  onDeleteReview = null,
  isDeletingId = null,
  loading = false
}) => {
  const totalPages = Math.ceil(total / pageSize) || 1;

  const handleSortChange = (e) => {
    if (onSortChange) {
      onSortChange(e.target.value);
    }
  };

  return (
    <div className="review-list-container">
      {/* List Header: Title, Total & Sort Control */}
      <div
        className="review-list-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 'var(--space-3)',
          marginBottom: 'var(--space-4)'
        }}
      >
        <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>
          Customer Reviews ({total})
        </h3>

        {total > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <label
              htmlFor="review-sort-select"
              style={{
                fontSize: '0.85rem',
                color: 'var(--color-text-secondary, #9ca3af)',
                fontWeight: 500
              }}
            >
              Sort by:
            </label>
            <select
              id="review-sort-select"
              className="input"
              value={sortBy}
              onChange={handleSortChange}
              disabled={loading}
              style={{
                padding: '4px 8px',
                fontSize: '0.85rem',
                borderRadius: '6px',
                width: 'auto'
              }}
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="highest_rating">Highest Rating</option>
              <option value="lowest_rating">Lowest Rating</option>
            </select>
          </div>
        )}
      </div>

      {/* Loading indicator */}
      {loading && (
        <div style={{ textAlign: 'center', padding: 'var(--space-8)' }}>
          <div className="spinner" style={{ margin: '0 auto var(--space-2)' }} />
          <p style={{ color: 'var(--color-text-secondary, #9ca3af)', fontSize: '0.9rem' }}>
            Loading reviews...
          </p>
        </div>
      )}

      {/* Empty State */}
      {!loading && reviews.length === 0 && (
        <div
          className="empty-state-box"
          style={{
            textAlign: 'center',
            padding: 'var(--space-8)',
          }}
        >
          <h4 style={{ margin: '0 0 var(--space-2)', fontSize: '1rem', fontWeight: 600 }}>No Reviews Yet</h4>
          <p
            style={{
              margin: 0,
              color: 'var(--color-text-secondary)',
              fontSize: '0.875rem'
            }}
          >
            No reviews have been submitted for this product yet.
          </p>
        </div>
      )}

      {/* Review Cards */}
      {!loading && reviews.length > 0 && (
        <div className="review-cards-list">
          {reviews.map((review) => {
            const isSelf = currentUserId && review.user_id === currentUserId;
            return (
              <ReviewCard
                key={review.id}
                review={review}
                isCurrentUser={isSelf}
                onEdit={onEditReview}
                onDelete={onDeleteReview}
                isDeleting={isDeletingId === review.id}
              />
            );
          })}
        </div>
      )}

      {/* Pagination Controls */}
      {!loading && totalPages > 1 && (
        <div
          className="reviews-pagination"
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 'var(--space-3)',
            marginTop: 'var(--space-6)'
          }}
        >
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
          >
            ← Previous
          </button>
          <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary, #9ca3af)' }}>
            Page {page} of {totalPages}
          </span>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
};

export default ReviewList;
