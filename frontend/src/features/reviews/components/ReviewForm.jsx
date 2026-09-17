import React, { useState, useEffect } from 'react';
import RatingStars from './RatingStars';

const RATING_LABELS = {
  1: 'Poor - Did not meet expectations',
  2: 'Fair - Below expectations',
  3: 'Average - Met expectations',
  4: 'Good - Exceeded expectations',
  5: 'Excellent - Highly recommended'
};

export const ReviewForm = ({
  initialReview = null,
  onSubmit,
  onCancel,
  isSubmitting = false,
  error = ''
}) => {
  const [rating, setRating] = useState(initialReview?.rating || 5);
  const [title, setTitle] = useState(initialReview?.title || '');
  const [comment, setComment] = useState(initialReview?.comment || '');
  const [validationError, setValidationError] = useState('');

  useEffect(() => {
    if (initialReview) {
      setRating(initialReview.rating || 5);
      setTitle(initialReview.title || '');
      setComment(initialReview.comment || '');
    }
  }, [initialReview]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setValidationError('');

    if (!rating || rating < 1 || rating > 5) {
      setValidationError('Please select a star rating between 1 and 5.');
      return;
    }

    onSubmit({
      rating: Number(rating),
      title: title.trim() || null,
      comment: comment.trim() || null
    });
  };

  return (
    <div
      className="review-form-card card"
      style={{
        padding: 'var(--space-6)',
        marginBottom: 'var(--space-6)',
        border: '1px solid var(--color-primary-subtle, rgba(99, 102, 241, 0.3))',
        background: 'var(--color-bg-secondary, rgba(255, 255, 255, 0.02))'
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 'var(--space-4)'
        }}
      >
        <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>
          {initialReview ? 'Edit Your Review' : 'Write a Verified Review'}
        </h3>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="btn btn-outline btn-sm"
            disabled={isSubmitting}
          >
            Cancel
          </button>
        )}
      </div>

      {(error || validationError) && (
        <div
          className="alert alert-error"
          style={{
            padding: 'var(--space-3)',
            marginBottom: 'var(--space-4)',
            borderRadius: '6px',
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#f87171',
            fontSize: '0.875rem'
          }}
        >
          {validationError || error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Star Rating Selector */}
        <div className="form-group" style={{ marginBottom: 'var(--space-4)' }}>
          <label
            style={{
              display: 'block',
              fontWeight: 600,
              fontSize: '0.9rem',
              marginBottom: 'var(--space-2)'
            }}
          >
            Your Rating <span style={{ color: 'var(--color-danger, #ef4444)' }}>*</span>
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <RatingStars
              rating={rating}
              size="lg"
              interactive={!isSubmitting}
              onChange={(val) => setRating(val)}
            />
            <span
              style={{
                fontSize: '0.85rem',
                color: 'var(--color-text-secondary, #9ca3af)',
                fontWeight: 500
              }}
            >
              {RATING_LABELS[rating] || ''}
            </span>
          </div>
        </div>

        {/* Review Title */}
        <div className="form-group" style={{ marginBottom: 'var(--space-4)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-1)' }}>
            <label
              htmlFor="review-title-input"
              style={{ fontWeight: 600, fontSize: '0.9rem' }}
            >
              Review Title (Optional)
            </label>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary, #9ca3af)' }}>
              {title.length}/100
            </span>
          </div>
          <input
            id="review-title-input"
            type="text"
            className="input"
            maxLength={100}
            placeholder="e.g. Blazing fast, runs whisper quiet at 1440p"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={isSubmitting}
            style={{ width: '100%' }}
          />
        </div>

        {/* Review Comment */}
        <div className="form-group" style={{ marginBottom: 'var(--space-4)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-1)' }}>
            <label
              htmlFor="review-comment-input"
              style={{ fontWeight: 600, fontSize: '0.9rem' }}
            >
              Detailed Review (Optional)
            </label>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary, #9ca3af)' }}>
              {comment.length}/2000
            </span>
          </div>
          <textarea
            id="review-comment-input"
            className="input"
            rows={4}
            maxLength={2000}
            placeholder="Tell other builders about build quality, noise levels, thermals, performance, ease of installation..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            disabled={isSubmitting}
            style={{ width: '100%', resize: 'vertical' }}
          />
        </div>

        {/* Submit & Cancel Buttons */}
        <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end' }}>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="btn btn-outline"
              disabled={isSubmitting}
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? 'Submitting...'
              : initialReview
              ? 'Update Review'
              : 'Submit Review'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ReviewForm;
