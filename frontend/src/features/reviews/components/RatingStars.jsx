import React, { useState } from 'react';

/**
 * RatingStars component
 * Can be interactive (input mode for review form) or read-only (display mode).
 */
export const RatingStars = ({
  rating = 0,
  maxRating = 5,
  size = 'md', // 'sm', 'md', 'lg'
  interactive = false,
  onChange = null,
  showValue = false,
  ariaLabel = 'Rating'
}) => {
  const [hoverRating, setHoverRating] = useState(0);

  const starSizes = {
    sm: '14px',
    md: '18px',
    lg: '24px'
  };

  const currentVal = interactive && hoverRating > 0 ? hoverRating : rating;

  const handleClick = (value) => {
    if (interactive && onChange) {
      onChange(value);
    }
  };

  const handleMouseEnter = (value) => {
    if (interactive) {
      setHoverRating(value);
    }
  };

  const handleMouseLeave = () => {
    if (interactive) {
      setHoverRating(0);
    }
  };

  return (
    <div
      className={`rating-stars-container rating-${size} ${interactive ? 'rating-interactive' : ''}`}
      style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
      role={interactive ? 'radiogroup' : 'img'}
      aria-label={`${ariaLabel}: ${rating} out of ${maxRating} stars`}
    >
      <div
        className="stars-wrapper"
        onMouseLeave={handleMouseLeave}
        style={{ display: 'inline-flex', gap: '2px' }}
      >
        {Array.from({ length: maxRating }, (_, index) => {
          const starValue = index + 1;
          const isFilled = currentVal >= starValue;
          const isHalf = !isFilled && currentVal >= starValue - 0.5;

          return (
            <button
              key={starValue}
              type="button"
              disabled={!interactive}
              onClick={() => handleClick(starValue)}
              onMouseEnter={() => handleMouseEnter(starValue)}
              className={`star-btn ${isFilled ? 'star-filled' : isHalf ? 'star-half' : 'star-empty'}`}
              style={{
                background: 'none',
                border: 'none',
                padding: '1px',
                cursor: interactive ? 'pointer' : 'default',
                fontSize: starSizes[size] || starSizes.md,
                color: isFilled || isHalf ? 'var(--color-warning, #f59e0b)' : 'var(--color-border-subtle, #4b5563)',
                lineHeight: 1,
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'transform 0.1s ease, color 0.15s ease'
              }}
              aria-label={`${starValue} star${starValue > 1 ? 's' : ''}`}
              role={interactive ? 'radio' : undefined}
              aria-checked={interactive ? rating === starValue : undefined}
            >
              ★
            </button>
          );
        })}
      </div>

      {showValue && (
        <span
          className="rating-value-badge"
          style={{
            marginLeft: '6px',
            fontSize: size === 'sm' ? '0.75rem' : size === 'lg' ? '1.1rem' : '0.875rem',
            fontWeight: 600,
            color: 'var(--color-text-primary, #f3f4f6)'
          }}
        >
          {Number(rating).toFixed(1)}
        </span>
      )}
    </div>
  );
};

export default RatingStars;
