import React, { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import { useCart } from '../../../context/CartContext';
import orderService from '../services/orderService';

export const CheckoutPage = () => {
  const { user } = useAuth();
  const { cart, loading: cartLoading, refreshCart } = useCart();
  const navigate = useNavigate();

  // Stable session idempotency key to prevent accidental duplicate submission
  const [idempotencyKey] = useState(() => {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return `key-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  });

  const [formData, setFormData] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    shipping_address_line1: '',
    shipping_address_line2: '',
    shipping_city: '',
    shipping_province: '',
    shipping_postal_code: '',
    shipping_country: 'Philippines',
    payment_method: 'COD',
  });

  const [errors, setErrors] = useState({});
  const [apiError, setApiError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Pre-fill customer information from user profile
  useEffect(() => {
    if (user) {
      const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ');
      setFormData((prev) => ({
        ...prev,
        customer_name: prev.customer_name || fullName,
        customer_email: prev.customer_email || user.email || '',
      }));
    }
  }, [user]);

  // Handle input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
    if (apiError) {
      setApiError('');
    }
  };

  // Client-side validation
  const validate = () => {
    const newErrors = {};
    if (!formData.customer_name.trim() || formData.customer_name.trim().length < 2) {
      newErrors.customer_name = 'Full name must be at least 2 characters.';
    }
    if (!formData.customer_email.trim() || !/\S+@\S+\.\S+/.test(formData.customer_email)) {
      newErrors.customer_email = 'Please enter a valid email address.';
    }
    if (!formData.customer_phone.trim() || formData.customer_phone.trim().length < 7) {
      newErrors.customer_phone = 'Please enter a valid phone number (at least 7 digits).';
    }
    if (!formData.shipping_address_line1.trim() || formData.shipping_address_line1.trim().length < 3) {
      newErrors.shipping_address_line1 = 'Street address is required.';
    }
    if (!formData.shipping_city.trim()) {
      newErrors.shipping_city = 'City / Municipality is required.';
    }
    if (!formData.shipping_province.trim()) {
      newErrors.shipping_province = 'Province / Region is required.';
    }
    if (!formData.shipping_postal_code.trim()) {
      newErrors.shipping_postal_code = 'Postal code is required.';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Submit checkout
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    setApiError('');

    try {
      const order = await orderService.checkout(
        {
          ...formData,
          idempotency_key: idempotencyKey,
        },
        idempotencyKey
      );

      // Successfully placed order!
      await refreshCart();
      navigate(`/orders/${order.order_number}/confirmation`, {
        state: { order },
        replace: true,
      });
    } catch (err) {
      const detail =
        err.response?.data?.detail ||
        'An error occurred while placing your order. Please review your cart and try again.';
      setApiError(detail);
      // Refresh cart to show updated stock or availability status
      await refreshCart();
    } finally {
      setSubmitting(false);
    }
  };

  if (cartLoading) {
    return (
      <div className="container page-wrapper">
        <div style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
          <p>Loading checkout...</p>
        </div>
      </div>
    );
  }

  const items = cart?.items || [];
  const hasUnavailableItems = items.some((i) => !i.is_available);

  if (items.length === 0) {
    return (
      <div className="container page-wrapper">
        <div className="card checkout-empty-card" style={{ textAlign: 'center', padding: 'var(--space-10)' }}>
          <h2 style={{ fontSize: '1.5rem', marginBottom: 'var(--space-3)' }}>Your Cart is Empty</h2>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-6)' }}>
            You do not have any items in your cart to checkout.
          </p>
          <Link to="/products" className="btn btn-primary">
            Browse Products
          </Link>
        </div>
      </div>
    );
  }

  const formattedSubtotal = Number(cart?.subtotal || 0).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });

  return (
    <div className="container page-wrapper">
      <div className="checkout-header" style={{ marginBottom: 'var(--space-6)' }}>
        <h1 className="page-title">Checkout</h1>
        <p className="page-subtitle">Complete your order details and delivery information.</p>
      </div>

      {apiError && (
        <div className="alert alert-danger" style={{ marginBottom: 'var(--space-6)' }}>
          <span>{apiError}</span>
        </div>
      )}

      {hasUnavailableItems && (
        <div className="alert alert-warning" style={{ marginBottom: 'var(--space-6)' }}>
          <span>
            Some items in your cart have availability changes. Please{' '}
            <Link to="/cart" style={{ textDecoration: 'underline' }}>
              review your cart
            </Link>{' '}
            before placing the order.
          </span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="checkout-grid">
          {/* Left Column: Information & Payment */}
          <div className="checkout-main-col">
            {/* Contact Information */}
            <div className="card checkout-section-card">
              <h2 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>
                1. Contact Information
              </h2>
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="customer_name" className="form-label">
                    Full Name <span style={{ color: 'var(--color-danger)' }}>*</span>
                  </label>
                  <input
                    id="customer_name"
                    name="customer_name"
                    type="text"
                    className={`form-input ${errors.customer_name ? 'input-error' : ''}`}
                    placeholder="e.g. Jane Doe"
                    value={formData.customer_name}
                    onChange={handleChange}
                    disabled={submitting}
                  />
                  {errors.customer_name && <span className="field-error">{errors.customer_name}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="customer_email" className="form-label">
                    Email Address <span style={{ color: 'var(--color-danger)' }}>*</span>
                  </label>
                  <input
                    id="customer_email"
                    name="customer_email"
                    type="email"
                    className={`form-input ${errors.customer_email ? 'input-error' : ''}`}
                    placeholder="e.g. jane@example.com"
                    value={formData.customer_email}
                    onChange={handleChange}
                    disabled={submitting}
                  />
                  {errors.customer_email && <span className="field-error">{errors.customer_email}</span>}
                </div>

                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label htmlFor="customer_phone" className="form-label">
                    Phone Number <span style={{ color: 'var(--color-danger)' }}>*</span>
                  </label>
                  <input
                    id="customer_phone"
                    name="customer_phone"
                    type="tel"
                    className={`form-input ${errors.customer_phone ? 'input-error' : ''}`}
                    placeholder="e.g. +63 917 123 4567"
                    value={formData.customer_phone}
                    onChange={handleChange}
                    disabled={submitting}
                  />
                  {errors.customer_phone && <span className="field-error">{errors.customer_phone}</span>}
                </div>
              </div>
            </div>

            {/* Shipping Address */}
            <div className="card checkout-section-card" style={{ marginTop: 'var(--space-6)' }}>
              <h2 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>
                2. Shipping Address
              </h2>
              <div className="form-grid">
                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label htmlFor="shipping_address_line1" className="form-label">
                    Street Address <span style={{ color: 'var(--color-danger)' }}>*</span>
                  </label>
                  <input
                    id="shipping_address_line1"
                    name="shipping_address_line1"
                    type="text"
                    className={`form-input ${errors.shipping_address_line1 ? 'input-error' : ''}`}
                    placeholder="House / Unit / Bldg No., Street name"
                    value={formData.shipping_address_line1}
                    onChange={handleChange}
                    disabled={submitting}
                  />
                  {errors.shipping_address_line1 && (
                    <span className="field-error">{errors.shipping_address_line1}</span>
                  )}
                </div>

                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label htmlFor="shipping_address_line2" className="form-label">
                    Apartment, Suite, Landmark (Optional)
                  </label>
                  <input
                    id="shipping_address_line2"
                    name="shipping_address_line2"
                    type="text"
                    className="form-input"
                    placeholder="e.g. Unit 4B, Near City Hall"
                    value={formData.shipping_address_line2}
                    onChange={handleChange}
                    disabled={submitting}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="shipping_city" className="form-label">
                    City / Municipality <span style={{ color: 'var(--color-danger)' }}>*</span>
                  </label>
                  <input
                    id="shipping_city"
                    name="shipping_city"
                    type="text"
                    className={`form-input ${errors.shipping_city ? 'input-error' : ''}`}
                    placeholder="e.g. Quezon City"
                    value={formData.shipping_city}
                    onChange={handleChange}
                    disabled={submitting}
                  />
                  {errors.shipping_city && <span className="field-error">{errors.shipping_city}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="shipping_province" className="form-label">
                    Province / Region <span style={{ color: 'var(--color-danger)' }}>*</span>
                  </label>
                  <input
                    id="shipping_province"
                    name="shipping_province"
                    type="text"
                    className={`form-input ${errors.shipping_province ? 'input-error' : ''}`}
                    placeholder="e.g. Metro Manila"
                    value={formData.shipping_province}
                    onChange={handleChange}
                    disabled={submitting}
                  />
                  {errors.shipping_province && (
                    <span className="field-error">{errors.shipping_province}</span>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="shipping_postal_code" className="form-label">
                    Postal Code <span style={{ color: 'var(--color-danger)' }}>*</span>
                  </label>
                  <input
                    id="shipping_postal_code"
                    name="shipping_postal_code"
                    type="text"
                    className={`form-input ${errors.shipping_postal_code ? 'input-error' : ''}`}
                    placeholder="e.g. 1100"
                    value={formData.shipping_postal_code}
                    onChange={handleChange}
                    disabled={submitting}
                  />
                  {errors.shipping_postal_code && (
                    <span className="field-error">{errors.shipping_postal_code}</span>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="shipping_country" className="form-label">
                    Country
                  </label>
                  <input
                    id="shipping_country"
                    name="shipping_country"
                    type="text"
                    className="form-input"
                    value={formData.shipping_country}
                    disabled
                  />
                </div>
              </div>
            </div>

            {/* Payment Method */}
            <div className="card checkout-section-card" style={{ marginTop: 'var(--space-6)' }}>
              <h2 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>
                3. Payment Method
              </h2>
              <div className="payment-method-selector">
                <label className="payment-option-card active">
                  <input
                    type="radio"
                    name="payment_method"
                    value="COD"
                    checked={formData.payment_method === 'COD'}
                    onChange={handleChange}
                    disabled={submitting}
                  />
                  <div className="payment-option-content">
                    <strong>Cash on Delivery (COD)</strong>
                    <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginTop: '0.25rem' }}>
                      Pay in cash upon courier parcel arrival. (Online payment methods like Card, GCash, and Maya will be integrated in subsequent releases).
                    </p>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Right Column: Order Review & Placement */}
          <div className="checkout-summary-col">
            <div className="card checkout-summary-card">
              <h2 className="cart-summary-title">Order Review</h2>

              <div className="checkout-items-list">
                {items.map((item) => (
                  <div key={item.id} className="checkout-item-row">
                    <div className="checkout-item-info">
                      <span className="checkout-item-name">{item.product.name}</span>
                      <span className="checkout-item-meta">
                        Qty: {item.quantity} × {Number(item.product.price).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                      </span>
                    </div>
                    <span className="checkout-item-subtotal">
                      {Number(item.item_subtotal).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                    </span>
                  </div>
                ))}
              </div>

              <div className="cart-summary-total-divider"></div>

              <div className="cart-summary-breakdown">
                <div className="summary-row">
                  <span className="summary-label">Subtotal</span>
                  <span className="summary-val">{formattedSubtotal}</span>
                </div>
                <div className="summary-row">
                  <span className="summary-label">Shipping</span>
                  <span className="summary-val" style={{ color: 'var(--color-success)' }}>Free ($0.00)</span>
                </div>
              </div>

              <div className="cart-summary-total-divider"></div>

              <div className="summary-row summary-total-row">
                <span className="summary-total-label">Total Amount</span>
                <span className="summary-total-val">{formattedSubtotal}</span>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block checkout-submit-btn"
                disabled={submitting || hasUnavailableItems}
              >
                {submitting ? 'Placing Order...' : `Place Order (${formattedSubtotal})`}
              </button>

              <p className="checkout-guarantee-note">
                Prices and inventory are verified upon order placement.
              </p>

              <Link
                to="/cart"
                className="btn btn-ghost btn-sm btn-block"
                style={{ textAlign: 'center', marginTop: 'var(--space-2)' }}
              >
                ← Return to Cart
              </Link>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default CheckoutPage;
