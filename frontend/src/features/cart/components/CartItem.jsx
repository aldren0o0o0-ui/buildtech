import React, { useState } from 'react';
import { Link } from 'react-router-dom';

export const CartItem = ({
  item,
  onUpdateQuantity,
  onRemove,
  disabled = false,
}) => {
  const [imgError, setImgError] = useState(false);
  const { product, quantity, is_available, availability_reason, item_subtotal } = item;

  const formattedUnitPrice = Number(product.price).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });

  const formattedSubtotal = Number(item_subtotal).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });

  const handleDecrement = () => {
    if (quantity > 1 && !disabled) {
      onUpdateQuantity(item.id, quantity - 1);
    }
  };

  const handleIncrement = () => {
    if (!disabled) {
      onUpdateQuantity(item.id, quantity + 1);
    }
  };

  return (
    <div className={`cart-item-row ${!is_available ? 'cart-item-unavailable' : ''}`}>
      {/* Product Image */}
      <div className="cart-item-image-wrapper">
        {product.image_url && !imgError ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="cart-item-image"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="cart-item-placeholder">
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

      {/* Product Details */}
      <div className="cart-item-details">
        <div className="cart-item-meta">
          {product.brand?.name && (
            <span className="cart-item-brand">{product.brand.name}</span>
          )}
          <span className="cart-item-sku">SKU: {product.sku}</span>
        </div>

        <Link to={`/products/${product.slug}`} className="cart-item-title">
          {product.name}
        </Link>

        {/* Availability Warning */}
        {!is_available && (
          <div className="cart-item-warning-text">
            <span>{availability_reason || 'Unavailable'}</span>
          </div>
        )}
      </div>

      {/* Unit Price */}
      <div className="cart-item-unit-price">
        <span className="cart-col-label">Price:</span>
        <span className="price-val">{formattedUnitPrice}</span>
      </div>

      {/* Quantity Stepper */}
      <div className="cart-item-quantity-col">
        <span className="cart-col-label">Qty:</span>
        <div className="quantity-stepper">
          <button
            type="button"
            onClick={handleDecrement}
            disabled={quantity <= 1 || disabled}
            className="stepper-btn"
            aria-label="Decrease quantity"
          >
            −
          </button>
          <span className="stepper-value" aria-live="polite">
            {quantity}
          </span>
          <button
            type="button"
            onClick={handleIncrement}
            disabled={disabled}
            className="stepper-btn"
            aria-label="Increase quantity"
          >
            +
          </button>
        </div>
      </div>

      {/* Item Subtotal */}
      <div className="cart-item-subtotal-col">
        <span className="cart-col-label">Subtotal:</span>
        <span className="subtotal-val">{formattedSubtotal}</span>
      </div>

      {/* Remove Action */}
      <div className="cart-item-actions-col">
        <button
          type="button"
          onClick={() => onRemove(item.id)}
          disabled={disabled}
          className="cart-remove-btn"
          aria-label={`Remove ${product.name} from cart`}
          title="Remove item"
        >
          ✕
        </button>
      </div>
    </div>
  );
};

export default CartItem;
