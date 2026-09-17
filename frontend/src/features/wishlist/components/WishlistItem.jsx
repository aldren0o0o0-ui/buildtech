import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useCart } from '../../../context/CartContext';
import { useWishlist } from '../../../context/WishlistContext';

export const WishlistItem = ({ item }) => {
  const { product } = item;
  const { addToCart, actionLoading: cartLoading } = useCart();
  const { removeFromWishlist, actionLoading: wishlistLoading } = useWishlist();

  const [imgError, setImgError] = useState(false);
  const [addingToCart, setAddingToCart] = useState(false);
  const [addedSuccess, setAddedSuccess] = useState(false);
  const [removing, setRemoving] = useState(false);

  const formattedPrice = Number(product.price).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });

  const handleAddToCart = async () => {
    if (!product.is_available) return;
    setAddingToCart(true);
    const result = await addToCart(product.id, 1);
    setAddingToCart(false);
    if (result.success) {
      setAddedSuccess(true);
      setTimeout(() => setAddedSuccess(false), 2000);
    }
  };

  const handleRemove = async () => {
    setRemoving(true);
    await removeFromWishlist(item.id);
    setRemoving(false);
  };

  const renderAvailabilityBadge = () => {
    if (product.availability_status === 'IN_STOCK') {
      return <span className="badge badge-success">In Stock</span>;
    }
    if (product.availability_status === 'OUT_OF_STOCK') {
      return <span className="badge badge-warning">Out of Stock</span>;
    }
    return <span className="badge badge-danger">Unavailable</span>;
  };

  return (
    <div className="card wishlist-item-card">
      <div className="wishlist-item-image-box">
        {product.image_url && !imgError ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="wishlist-item-img"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="wishlist-placeholder-img">
            <svg
              viewBox="0 0 24 24"
              width="24"
              height="24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <rect x="4" y="4" width="16" height="16" rx="2" />
              <rect x="9" y="9" width="6" height="6" />
              <line x1="9" y1="1" x2="9" y2="4" />
              <line x1="15" y1="1" x2="15" y2="4" />
              <line x1="9" y1="20" x2="9" y2="23" />
              <line x1="15" y1="20" x2="15" y2="23" />
              <line x1="20" y1="9" x2="23" y2="9" />
              <line x1="20" y1="14" x2="23" y2="14" />
              <line x1="1" y1="9" x2="4" y2="9" />
              <line x1="1" y1="14" x2="4" y2="14" />
            </svg>
          </div>
        )}
      </div>

      <div className="wishlist-item-info">
        <div className="wishlist-item-meta">
          {product.brand?.name && (
            <span className="wishlist-brand-label">{product.brand.name}</span>
          )}
          {product.category?.name && (
            <span className="wishlist-category-label">{product.category.name}</span>
          )}
        </div>

        <Link
          to={`/products/${product.slug}`}
          className="wishlist-item-title"
          title={product.name}
        >
          {product.name}
        </Link>

        <div className="wishlist-item-sku">SKU: {product.sku}</div>

        <div className="wishlist-item-status-row">
          <span className="wishlist-item-price">{formattedPrice}</span>
          {renderAvailabilityBadge()}
        </div>
      </div>

      <div className="wishlist-item-actions">
        <button
          type="button"
          onClick={handleAddToCart}
          disabled={!product.is_available || addingToCart || cartLoading}
          className={`btn btn-sm ${
            addedSuccess ? 'btn-success' : 'btn-primary'
          } wishlist-cart-btn`}
        >
          {addedSuccess
            ? 'Added'
            : addingToCart
            ? 'Adding...'
            : !product.is_available
            ? 'Unavailable'
            : 'Add to Cart'}
        </button>

        <button
          type="button"
          onClick={handleRemove}
          disabled={removing || wishlistLoading}
          className="btn btn-outline btn-sm wishlist-remove-btn"
          title="Remove from wishlist"
          aria-label={`Remove ${product.name} from wishlist`}
        >
          {removing ? 'Removing...' : 'Remove'}
        </button>
      </div>
    </div>
  );
};

export default WishlistItem;
