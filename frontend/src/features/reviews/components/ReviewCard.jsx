import React from 'react';
import RatingStars from './RatingStars';

export const ReviewCard = ({ review, isCurrentUser = false, onEdit = null, onDelete = null, isDeleting = false }) => {
  if (!review) return null;

  const formatDate = (dateString) => {
    if (!dateString) return '';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div
      className={`review-card card ${isCurrentUser ? 'review-card-self' : ''}`}
      style={{
        padding: 'var(--space-5)',
        marginBottom: 'var(--space-4)',
        borderLeft: isCurrentUser ? '3px solid var(--color-primary, #6366f1)' : undefined,
        background: isCurrentUser ? 'rgba(99, 102, 241, 0.04)' : undefined
      }}
    >
      {/* Header: Stars, Rating, Badges, Date */}
      <div
        className="review-card-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 'var(--space-2)',
          marginBottom: 'var(--space-3)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          <RatingStars rating={review.rating} size="md" showValue />

          <div
            className="verified-purchase-pill"
            style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              padding: '2px 8px',
              borderRadius: '9999px',
              background: 'rgba(16, 185, 129, 0.12)',
              color: '#10b981',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            ✓ Verified Purchaser
          </div>

          {isCurrentUser && (
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                padding: '2px 8px',
                borderRadius: '9999px',
                background: 'rgba(99, 102, 241, 0.15)',
                color: '#818cf8',
                border: '1px solid rgba(99, 102, 241, 0.3)'
              }}
            >
              Your Review
            </span>
          )}
        </div>

        <div
          className="review-date"
          style={{
            fontSize: '0.8rem',
            color: 'var(--color-text-secondary, #9ca3af)'
          }}
        >
          {formatDate(review.created_at)}
          {review.updated_at && review.updated_at !== review.created_at && (
            <span style={{ fontStyle: 'italic', marginLeft: '4px' }}>(edited)</span>
          )}
        </div>
      </div>

      {/* Title */}
      {review.title && (
        <h4
          className="review-title"
          style={{
            fontSize: '1.05rem',
            fontWeight: 700,
            marginBottom: 'var(--space-2)',
            color: 'var(--color-text-primary, #f9fafb)'
          }}
        >
          {review.title}
        </h4>
      )}

      {/* Review Comment Body */}
      {review.comment && (
        <p
          className="review-comment"
          style={{
            fontSize: '0.925rem',
            lineHeight: 1.6,
            color: 'var(--color-text-secondary, #d1d5db)',
            whiteSpace: 'pre-line',
            margin: '0 0 var(--space-3) 0'
          }}
        >
          {review.comment}
        </p>
      )}

      {/* Footer: Author Name & Actions */}
      <div
        className="review-card-footer"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingTop: 'var(--space-3)',
          borderTop: '1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.06))',
          fontSize: '0.825rem',
          color: 'var(--color-text-secondary, #9ca3af)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span>By</span>
          <strong style={{ color: 'var(--color-text-primary, #e5e7eb)' }}>
            {review.author_name || 'Verified Customer'}
          </strong>
        </div>

        {isCurrentUser && (
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            {onEdit && (
              <button
                type="button"
                onClick={() => onEdit(review)}
                className="btn btn-outline btn-sm"
                style={{ fontSize: '0.75rem', padding: '3px 8px' }}
                disabled={isDeleting}
              >
                Edit
              </button>
            )}
            {onDelete && (
              <button
                type="button"
                onClick={() => onDelete(review.id)}
                className="btn btn-danger-outline btn-sm"
                style={{ fontSize: '0.75rem', padding: '3px 8px' }}
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ReviewCard;
