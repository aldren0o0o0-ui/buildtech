import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useCart } from '../../../context/CartContext';
import { WishlistButton } from '../../wishlist';

export const ProductCard = ({ product }) => {
  const [imgError, setImgError] = useState(false);
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);

  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { addToCart } = useCart();

  const formattedPrice = Number(product.price).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });

  const handleQuickAdd = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    if (user?.role === 'ADMIN') {
      return;
    }

    setAdding(true);
    const result = await addToCart(product.id, 1);
    setAdding(false);

    if (result.success) {
      setAdded(true);
      setTimeout(() => setAdded(false), 1800);
    }
  };

  return (
    <Link
      to={`/products/${product.slug}`}
      className="product-card"
      aria-label={`View details for ${product.name}`}
    >
      <div className="product-card-image-wrapper">
        <WishlistButton
          productId={product.id}
          variant="icon"
          className="product-card-wishlist-btn"
        />
        {product.image_url && !imgError ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="product-card-image"
            loading="lazy"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="product-card-placeholder">
            <svg className="product-placeholder-svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <rect x="4" y="4" width="16" height="16" rx="2" />
              <rect x="9" y="9" width="6" height="6" />
              <line x1="9" y1="1" x2="9" y2="4" />
              <line x1="15" y1="1" x2="15" y2="4" />
              <line x1="9" y1="20" x2="9" y2="23" />
              <line x1="15" y1="20" x2="15" y2="23" />
              <line x1="20" y1="9" x2="23" y2="9" />
              <line x1="20" y1="15" x2="23" y2="15" />
              <line x1="1" y1="9" x2="4" y2="9" />
              <line x1="1" y1="15" x2="4" y2="15" />
            </svg>
            <span className="product-placeholder-text">Hardware</span>
          </div>
        )}
      </div>

      <div className="product-card-content">
        <div className="product-card-meta">
          {product.brand?.name && (
            <span className="product-card-brand">{product.brand.name}</span>
          )}
          {product.category?.name && (
            <span className="product-card-category">{product.category.name}</span>
          )}
        </div>

        <h3 className="product-card-title" title={product.name}>
          {product.name}
        </h3>

        <div className="product-card-footer">
          <span className="product-card-price">{formattedPrice}</span>
          {user?.role !== 'ADMIN' && (
            <button
              type="button"
              onClick={handleQuickAdd}
              disabled={adding}
              className={`btn btn-sm product-card-add-btn ${
                added ? 'btn-success' : 'btn-outline'
              }`}
              title="Add 1 unit to cart"
            >
              {added ? 'Added' : adding ? '...' : 'Add'}
            </button>
          )}
        </div>
      </div>
    </Link>
  );
};

export default ProductCard;
