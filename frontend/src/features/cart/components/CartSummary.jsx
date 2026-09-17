import React from 'react';
import { Link } from 'react-router-dom';

export const CartSummary = ({
  cart,
  onClearCart,
  disabled = false,
}) => {
  if (!cart) return null;

  const formattedSubtotal = Number(cart.subtotal).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });

  const hasUnavailableItems = cart.items.some((i) => !i.is_available);

  return (
    <div className="card cart-summary-card">
      <h2 className="cart-summary-title">Order Summary</h2>

      <div className="cart-summary-breakdown">
        <div className="summary-row">
          <span className="summary-label">Items ({cart.item_count})</span>
          <span className="summary-val">{cart.total_quantity} units</span>
        </div>

        <div className="summary-row">
          <span className="summary-label">Subtotal</span>
          <span className="summary-val summary-subtotal">{formattedSubtotal}</span>
        </div>

        <div className="summary-row summary-note-row">
          <span className="summary-label">Shipping & Taxes</span>
          <span className="summary-val summary-muted">Calculated at checkout</span>
        </div>
      </div>

      <div className="cart-summary-total-divider"></div>

      <div className="summary-row summary-total-row">
        <span className="summary-total-label">Estimated Total</span>
        <span className="summary-total-val">{formattedSubtotal}</span>
      </div>

      {/* Checkout Action */}
      <div className="cart-checkout-box">
        {hasUnavailableItems || cart.items.length === 0 || disabled ? (
          <button
            type="button"
            className="btn btn-primary btn-block"
            disabled
            title={
              hasUnavailableItems
                ? 'Please resolve unavailable items before proceeding'
                : 'Your cart is empty'
            }
          >
            Proceed to Checkout
          </button>
        ) : (
          <Link
            to="/checkout"
            className="btn btn-primary btn-block"
            style={{ textAlign: 'center', textDecoration: 'none' }}
          >
            Proceed to Checkout
          </Link>
        )}
        <p className="checkout-helper-note">
          Prices and inventory are verified upon checkout.
        </p>
      </div>

      {/* Secondary Actions */}
      <div className="cart-summary-actions">
        <button
          type="button"
          onClick={onClearCart}
          disabled={disabled}
          className="btn btn-ghost btn-sm btn-block"
        >
          Clear Cart
        </button>

        <Link
          to="/products"
          className="btn btn-outline btn-sm btn-block"
          style={{ textAlign: 'center', textDecoration: 'none' }}
        >
          ← Continue Shopping
        </Link>
      </div>
    </div>
  );
};

export default CartSummary;
