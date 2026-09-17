import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useWishlist } from '../../../context/WishlistContext';

const HeartIcon = ({ filled }) => (
  <svg
    viewBox="0 0 24 24"
    width="15"
    height="15"
    fill={filled ? 'currentColor' : 'none'}
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
  </svg>
);

export const WishlistButton = ({
  productId,
  variant = 'icon', // 'icon' | 'full'
  className = '',
}) => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { isWishlisted, toggleWishlist } = useWishlist();

  const [loading, setLoading] = useState(false);

  const active = isWishlisted(productId);

  const handleClick = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    if (user?.role === 'ADMIN') {
      return;
    }

    if (loading) return;

    setLoading(true);
    await toggleWishlist(productId);
    setLoading(false);
  };

  if (user?.role === 'ADMIN') {
    return null;
  }

  if (variant === 'full') {
    return (
      <button
        type="button"
        onClick={handleClick}
        disabled={loading}
        className={`btn wishlist-btn-full ${active ? 'active' : ''} ${className}`}
        aria-label={active ? 'Remove from wishlist' : 'Add to wishlist'}
        aria-pressed={active}
        title={active ? 'Remove from wishlist' : 'Save to wishlist'}
      >
        <span className="wishlist-btn-icon" aria-hidden="true" style={{ display: 'inline-flex', alignItems: 'center' }}>
          <HeartIcon filled={active} />
        </span>
        <span className="wishlist-btn-text">
          {loading
            ? 'Updating...'
            : active
            ? 'Saved to Wishlist'
            : 'Add to Wishlist'}
        </span>
      </button>
    );
  }

  // Icon-only variant (used on ProductCard)
  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      className={`wishlist-btn-icon-only ${active ? 'active' : ''} ${className}`}
      aria-label={active ? 'Remove from wishlist' : 'Add to wishlist'}
      aria-pressed={active}
      title={active ? 'Remove from wishlist' : 'Save to wishlist'}
    >
      <span className="wishlist-icon" aria-hidden="true" style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
        <HeartIcon filled={active} />
      </span>
    </button>
  );
};

export default WishlistButton;
