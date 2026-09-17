import React from 'react';
import RatingStars from './RatingStars';

export const ReviewSummary = ({ summary, onWriteReviewClick, canReview, hasReviewed, isAuthenticated: _isAuthenticated }) => {
  if (!summary) {
    return null;
  }

  const { average_rating = 0, total_reviews = 0, rating_distribution = {} } = summary;

  const distribution = [5, 4, 3, 2, 1].map((stars) => {
    const count = rating_distribution[stars] || 0;
    const percentage = total_reviews > 0 ? Math.round((count / total_reviews) * 100) : 0;
    return { stars, count, percentage };
  });

  return (
    <div className="review-summary-card card" style={{ padding: 'var(--space-6)', marginBottom: 'var(--space-8)' }}>
      <div
        className="review-summary-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 'var(--space-6)',
          alignItems: 'center'
        }}
      >
        {/* Overall Rating Block */}
        <div
          className="review-overall-block"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            padding: 'var(--space-4)',
            borderRight: '1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.08))'
          }}
        >
          <div
            className="review-avg-number"
            style={{
              fontSize: '3.5rem',
              fontWeight: 800,
              lineHeight: 1,
              color: 'var(--color-primary, #6366f1)',
              marginBottom: 'var(--space-2)'
            }}
          >
            {Number(average_rating).toFixed(1)}
          </div>
          <RatingStars rating={average_rating} size="lg" />
          <div
            className="review-total-count"
            style={{
              marginTop: 'var(--space-2)',
              fontSize: '0.9rem',
              color: 'var(--color-text-secondary, #9ca3af)'
            }}
          >
            Based on {total_reviews} {total_reviews === 1 ? 'review' : 'reviews'}
          </div>

          <div
            className="verified-guarantee-badge"
            style={{
              marginTop: 'var(--space-4)',
              padding: '4px 10px',
              borderRadius: '9999px',
              fontSize: '0.75rem',
              fontWeight: 500,
              background: 'rgba(16, 185, 129, 0.1)',
              color: '#10b981',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            ✓ Verified Purchasers Only
          </div>
        </div>

        {/* Rating Breakdown Distribution */}
        <div className="review-distribution-block" style={{ flex: 1 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {distribution.map(({ stars, count, percentage }) => (
              <div
                key={stars}
                className="distribution-row"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-3)',
                  fontSize: '0.85rem'
                }}
              >
                <span style={{ minWidth: '45px', color: 'var(--color-text-secondary, #9ca3af)' }}>
                  {stars} ★
                </span>
                <div
                  className="distribution-bar-bg"
                  style={{
                    flex: 1,
                    height: '8px',
                    background: 'var(--color-bg-secondary, rgba(255, 255, 255, 0.06))',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}
                >
                  <div
                    className="distribution-bar-fill"
                    style={{
                      width: `${percentage}%`,
                      height: '100%',
                      background: 'var(--color-warning, #f59e0b)',
                      borderRadius: '4px',
                      transition: 'width 0.4s ease'
                    }}
                  />
                </div>
                <span
                  style={{
                    minWidth: '40px',
                    textAlign: 'right',
                    color: 'var(--color-text-secondary, #9ca3af)',
                    fontSize: '0.8rem'
                  }}
                >
                  {percentage}% ({count})
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Action Callout Block */}
        <div
          className="review-action-block"
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            padding: 'var(--space-4)',
            gap: 'var(--space-3)'
          }}
        >
          <h4 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 600 }}>Have you purchased this product?</h4>
          <p
            style={{
              margin: 0,
              fontSize: '0.85rem',
              color: 'var(--color-text-secondary, #9ca3af)',
              maxWidth: '240px'
            }}
          >
            {hasReviewed
              ? 'You have already shared your thoughts on this item.'
              : canReview
              ? 'Share your feedback on this product.'
              : 'Purchasers with confirmed orders are eligible to write a review.'}
          </p>
          {onWriteReviewClick && (
            <button
              type="button"
              onClick={onWriteReviewClick}
              className={`btn ${hasReviewed ? 'btn-secondary' : 'btn-primary'}`}
              style={{ minWidth: '160px' }}
            >
              {hasReviewed ? 'Edit My Review' : 'Write a Review'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReviewSummary;
