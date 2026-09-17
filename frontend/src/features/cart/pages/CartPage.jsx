import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useCart } from '../../../context/CartContext';
import CartItem from '../components/CartItem';
import CartSummary from '../components/CartSummary';
import EmptyCart from '../components/EmptyCart';
import CartAvailabilityMessage from '../components/CartAvailabilityMessage';

export const CartPage = () => {
  const {
    cart,
    loading,
    actionLoading,
    error,
    updateQuantity,
    removeItem,
    clearCart,
  } = useCart();

  const [feedbackError, setFeedbackError] = useState(null);

  const handleUpdateQuantity = async (itemId, newQty) => {
    setFeedbackError(null);
    const result = await updateQuantity(itemId, newQty);
    if (!result.success) {
      setFeedbackError(result.error);
    }
  };

  const handleRemoveItem = async (itemId) => {
    setFeedbackError(null);
    const result = await removeItem(itemId);
    if (!result.success) {
      setFeedbackError(result.error);
    }
  };

  const handleClearCart = async () => {
    if (window.confirm('Are you sure you want to remove all items from your cart?')) {
      setFeedbackError(null);
      const result = await clearCart();
      if (!result.success) {
        setFeedbackError(result.error);
      }
    }
  };

  if (loading && !cart) {
    return (
      <div className="container page-wrapper">
        <div className="spinner-wrapper" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true"></div>
          <p>Loading your shopping cart...</p>
        </div>
      </div>
    );
  }

  const isEmpty = !cart || cart.items.length === 0;

  return (
    <div className="container page-wrapper">
      {/* Breadcrumb Navigation */}
      <div className="product-detail-breadcrumb">
        <Link to="/products" className="back-link">
          ← Back to Catalog
        </Link>
        <span className="breadcrumb-separator">/</span>
        <span className="breadcrumb-current">Shopping Cart</span>
      </div>

      <div className="cart-page-header">
        <h1 className="cart-page-title">Shopping Cart</h1>
        {!isEmpty && (
          <p className="cart-page-subtitle">
            Review your selected components ({cart.total_quantity} {cart.total_quantity === 1 ? 'unit' : 'units'})
          </p>
        )}
      </div>

      {/* Error Alert */}
      {(error || feedbackError) && (
        <div className="alert alert-danger" role="alert">
          <span>{feedbackError || error}</span>
        </div>
      )}

      {/* Dynamic Item Availability Warnings */}
      {cart && <CartAvailabilityMessage items={cart.items} />}

      {/* Main Content */}
      {isEmpty ? (
        <EmptyCart />
      ) : (
        <div className="cart-layout-grid">
          {/* Items Column */}
          <div className="cart-items-container">
            <div className="cart-items-header">
              <span>Hardware Component</span>
              <span>Price</span>
              <span>Quantity</span>
              <span>Subtotal</span>
              <span></span>
            </div>

            <div className="cart-items-list">
              {cart.items.map((item) => (
                <CartItem
                  key={item.id}
                  item={item}
                  onUpdateQuantity={handleUpdateQuantity}
                  onRemove={handleRemoveItem}
                  disabled={actionLoading}
                />
              ))}
            </div>
          </div>

          {/* Summary Column */}
          <div className="cart-summary-container">
            <CartSummary
              cart={cart}
              onClearCart={handleClearCart}
              disabled={actionLoading}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default CartPage;
