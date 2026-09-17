import React from 'react';
import { useWishlist } from '../../../context/WishlistContext';
import WishlistItem from '../components/WishlistItem';
import WishlistEmpty from '../components/WishlistEmpty';

export const WishlistPage = () => {
  const { wishlist, loading, error, refreshWishlist } = useWishlist();

  const items = wishlist?.items || [];
  const itemCount = wishlist?.item_count || 0;

  return (
    <div className="container page-wrapper">
      <div className="wishlist-page-header">
        <div className="wishlist-header-left">
          <h1 className="wishlist-page-title">My Wishlist</h1>
          <p className="wishlist-page-subtitle">
            Manage your saved computer hardware components and track availability.
          </p>
        </div>
        {itemCount > 0 && (
          <div className="wishlist-header-badge">
            <span className="badge badge-primary">{itemCount} Saved</span>
          </div>
        )}
      </div>

      {error && (
        <div className="alert alert-danger" role="alert">
          <span>{error}</span>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={refreshWishlist}
            style={{ marginLeft: 'auto' }}
          >
            Retry
          </button>
        </div>
      )}

      {loading && !wishlist ? (
        <div className="wishlist-loading-grid" aria-busy="true">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card product-card-skeleton">
              <div className="skeleton-img"></div>
              <div className="skeleton-text"></div>
              <div className="skeleton-text short"></div>
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <WishlistEmpty />
      ) : (
        <div className="wishlist-grid">
          {items.map((item) => (
            <WishlistItem key={item.id} item={item} />
          ))}
        </div>
      )}
    </div>
  );
};

export default WishlistPage;
