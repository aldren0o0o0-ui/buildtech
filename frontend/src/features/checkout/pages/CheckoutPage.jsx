import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useCart } from '../../../context/CartContext';
import addressService from '../../addresses/services/addressService';
import checkoutService from '../services/checkoutService';
import orderService from '../../orders/services/orderService';
import AddressCard from '../../addresses/components/AddressCard';
import AddressForm from '../../addresses/components/AddressForm';

export const CheckoutPage = () => {
  const navigate = useNavigate();
  const { cart, loading: cartLoading, refreshCart } = useCart();

  // Address State
  const [addresses, setAddresses] = useState([]);
  const [selectedAddress, setSelectedAddress] = useState(null);
  const [addressesLoading, setAddressesLoading] = useState(true);
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [isChangingAddress, setIsChangingAddress] = useState(false);

  // Validation State
  const [validationResult, setValidationResult] = useState(null);
  const [validating, setValidating] = useState(false);
  const [validationError, setValidationError] = useState('');
  const [validationSuccess, setValidationSuccess] = useState(false);

  // Order Placement State
  const [orderNotes, setOrderNotes] = useState('');
  const [placingOrder, setPlacingOrder] = useState(false);
  const [placeOrderError, setPlaceOrderError] = useState('');

  // Fetch customer saved addresses
  const loadAddresses = useCallback(async () => {
    try {
      setAddressesLoading(true);
      const data = await addressService.getAddresses();
      setAddresses(data);
      if (data.length > 0) {
        // Prefer default address, or the first one
        const defaultAddr = data.find((a) => a.is_default) || data[0];
        setSelectedAddress(defaultAddr);
      }
    } catch (err) {
      setValidationError(
        err.response?.data?.detail || 'Failed to load saved shipping addresses.'
      );
    } finally {
      setAddressesLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAddresses();
  }, [loadAddresses]);

  // Run backend checkout validation whenever selectedAddress changes
  const runValidation = useCallback(
    async (addressId) => {
      if (!addressId) return;
      try {
        setValidating(true);
        setValidationError('');
        const res = await checkoutService.validateCheckout(addressId);
        setValidationResult(res);
        if (res.valid) {
          setValidationSuccess(true);
        } else {
          setValidationSuccess(false);
        }
      } catch (err) {
        setValidationError(
          err.response?.data?.detail ||
            'Checkout validation failed. Please check your cart and shipping address.'
        );
        setValidationResult(null);
        setValidationSuccess(false);
      } finally {
        setValidating(false);
      }
    },
    []
  );

  useEffect(() => {
    if (selectedAddress?.id && cart?.items?.length > 0) {
      runValidation(selectedAddress.id);
    }
  }, [selectedAddress?.id, cart?.items?.length, runValidation]);

  // Handle new address creation from checkout
  const handleCreateAddress = async (formData) => {
    try {
      setValidating(true);
      const newAddr = await addressService.createAddress(formData);
      await loadAddresses();
      setSelectedAddress(newAddr);
      setShowAddressForm(false);
      setIsChangingAddress(false);
    } catch (err) {
      setValidationError(
        err.response?.data?.detail || 'Failed to save new shipping address.'
      );
    } finally {
      setValidating(false);
    }
  };

  // Handle Authoritative Module 10 Order Placement
  const handlePlaceOrder = async () => {
    if (!selectedAddress || !validationResult?.valid) return;
    setPlacingOrder(true);
    setPlaceOrderError('');
    try {
      const idempotencyKey = `BT-ORDER-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      const order = await orderService.createOrder(
        {
          address_id: selectedAddress.id,
          payment_method: 'COD',
          notes: orderNotes.trim() || undefined,
        },
        idempotencyKey
      );
      // Synchronize cart state
      await refreshCart();
      // Redirect to confirmation page
      navigate(`/orders/${order.order_number}/confirmation`);
    } catch (err) {
      setPlaceOrderError(
        err.response?.data?.detail || 'Failed to place order. Please check available stock and try again.'
      );
    } finally {
      setPlacingOrder(false);
    }
  };

  if (cartLoading || addressesLoading) {
    return (
      <div className="container page-wrapper">
        <div style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
          <p>Loading checkout details...</p>
        </div>
      </div>
    );
  }

  const items = cart?.items || [];

  if (items.length === 0) {
    return (
      <div className="container page-wrapper">
        <div className="empty-state-box">
          <svg
            className="empty-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <circle cx="9" cy="21" r="1" />
            <circle cx="20" cy="21" r="1" />
            <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
          </svg>
          <h2 className="empty-title">Your Cart is Empty</h2>
          <p className="empty-desc">
            You do not have any items in your cart to checkout.
          </p>
          <Link to="/products" className="btn btn-primary btn-sm">
            Browse Products
          </Link>
        </div>
      </div>
    );
  }

  const displayItems = validationResult?.items || items.map((i) => ({
    cart_item_id: i.id,
    product_id: i.product.id,
    product_name: i.product.name,
    sku: i.product.sku,
    quantity: i.quantity,
    unit_price: i.product.price,
    item_subtotal: i.item_subtotal,
    is_available: i.is_available,
    status: i.availability_status || (i.is_available ? 'AVAILABLE' : 'INSUFFICIENT_STOCK'),
  }));

  const authoritativeSubtotal = Number(validationResult?.subtotal || cart?.subtotal || 0).toLocaleString(
    'en-US',
    { style: 'currency', currency: 'USD' }
  );

  const authoritativeShipping = Number(validationResult?.shipping_fee || 0).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });

  const authoritativeTotal = Number(validationResult?.total || cart?.subtotal || 0).toLocaleString(
    'en-US',
    { style: 'currency', currency: 'USD' }
  );

  const hasIssues = validationResult && (!validationResult.valid || validationResult.issues?.length > 0);

  return (
    <div className="container page-wrapper">
      <div className="page-header" style={{ marginBottom: 'var(--space-6)' }}>
        <h1 className="page-title">Checkout</h1>
        <p className="page-description">
          Review your shipping address and order details before placing your order.
        </p>
      </div>

      {/* Global Validation Alert */}
      {validationError && (
        <div className="alert alert-danger" role="alert" style={{ marginBottom: 'var(--space-6)' }}>
          <span>{validationError}</span>
        </div>
      )}

      {hasIssues && (
        <div className="alert alert-warning" role="alert" style={{ marginBottom: 'var(--space-6)' }}>
          <div>
            <strong>Checkout Issues Detected:</strong>
            <ul style={{ margin: 'var(--space-2) 0 0 var(--space-4)' }}>
              {validationResult.issues.map((issue, idx) => (
                <li key={idx}>{issue.message}</li>
              ))}
            </ul>
          </div>
          <div style={{ marginTop: 'var(--space-3)' }}>
            <Link to="/cart" className="btn btn-sm btn-outline">
              ← Return to Cart to Resolve
            </Link>
          </div>
        </div>
      )}

      <div className="checkout-layout">
        {/* Left Column: Address & Items */}
        <div className="checkout-main">
          {/* Section 1: Shipping Address */}
          <div className="card checkout-section-card">
            <div className="checkout-section-header">
              <h2 className="card-title">Shipping Address</h2>
              {selectedAddress && !isChangingAddress && !showAddressForm && (
                <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => setIsChangingAddress(true)}
                  >
                    Change Address
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline btn-sm"
                    onClick={() => {
                      setShowAddressForm(true);
                      setIsChangingAddress(false);
                    }}
                  >
                    + Add New
                  </button>
                </div>
              )}
            </div>

            {/* Address Selection Mode */}
            {isChangingAddress && (
              <div className="address-selection-list">
                <p className="form-helper" style={{ marginBottom: 'var(--space-3)' }}>
                  Select an address for delivery:
                </p>
                <div className="address-grid">
                  {addresses.map((addr) => (
                    <AddressCard
                      key={addr.id}
                      address={addr}
                      selectable
                      selected={selectedAddress?.id === addr.id}
                      onSelect={(chosen) => {
                        setSelectedAddress(chosen);
                        setIsChangingAddress(false);
                      }}
                    />
                  ))}
                </div>
                <div style={{ marginTop: 'var(--space-4)', display: 'flex', gap: 'var(--space-2)' }}>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => setIsChangingAddress(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline btn-sm"
                    onClick={() => {
                      setShowAddressForm(true);
                      setIsChangingAddress(false);
                    }}
                  >
                    + Add New Address
                  </button>
                </div>
              </div>
            )}

            {/* Address Form (Add New inline) */}
            {showAddressForm && (
              <div style={{ marginTop: 'var(--space-4)' }}>
                <AddressForm
                  onSubmit={handleCreateAddress}
                  onCancel={() => setShowAddressForm(false)}
                  loading={validating}
                  title="Add Delivery Address"
                />
              </div>
            )}

            {/* Selected Address Display */}
            {!isChangingAddress && !showAddressForm && (
              <>
                {selectedAddress ? (
                  <AddressCard address={selectedAddress} />
                ) : (
                  <div style={{ textAlign: 'center', padding: 'var(--space-6)' }}>
                    <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-4)' }}>
                      No shipping address found. Please add an address to continue.
                    </p>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => setShowAddressForm(true)}
                    >
                      + Add Shipping Address
                    </button>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Section 2: Order Items Preview */}
          <div className="card checkout-section-card" style={{ marginTop: 'var(--space-6)' }}>
            <div className="checkout-section-header">
              <h2 className="card-title">Order Items ({displayItems.length})</h2>
              <Link to="/cart" className="btn btn-ghost btn-sm">
                Edit Cart
              </Link>
            </div>

            <div className="checkout-items-list">
              {displayItems.map((item) => {
                const isItemAvailable = item.is_available !== false;
                const formattedUnitPrice = Number(item.unit_price).toLocaleString('en-US', {
                  style: 'currency',
                  currency: 'USD',
                });
                const formattedItemSubtotal = Number(item.item_subtotal).toLocaleString('en-US', {
                  style: 'currency',
                  currency: 'USD',
                });

                return (
                  <div
                    key={item.cart_item_id || item.product_id}
                    className={`checkout-item-row ${!isItemAvailable ? 'item-row-warning' : ''}`}
                  >
                    <div className="checkout-item-info">
                      <span className="checkout-item-name">{item.product_name}</span>
                      <span className="checkout-item-sku">SKU: {item.sku}</span>
                      {!isItemAvailable && (
                        <span className="badge badge-danger checkout-item-status-pill">
                          {item.status === 'OUT_OF_STOCK'
                            ? 'Out of Stock'
                            : item.status === 'PRODUCT_UNAVAILABLE'
                            ? 'Unavailable'
                            : 'Insufficient Stock'}
                        </span>
                      )}
                    </div>
                    <div className="checkout-item-qty">
                      Qty: <strong>{item.quantity}</strong>
                    </div>
                    <div className="checkout-item-price">
                      <span className="unit-price">{formattedUnitPrice} each</span>
                      <span className="item-subtotal">{formattedItemSubtotal}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Section 3: Payment Method */}
          <div className="card checkout-section-card" style={{ marginTop: 'var(--space-6)' }}>
            <h2 className="card-title">Payment Method</h2>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-3)',
              padding: 'var(--space-4)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-surface-muted)',
              marginTop: 'var(--space-3)',
            }}>
              <input
                type="radio"
                id="payment-cod"
                name="payment_method"
                checked={true}
                readOnly
              />
              <label htmlFor="payment-cod" style={{ fontWeight: '500', cursor: 'pointer', flex: 1 }}>
                Cash on Delivery (COD)
                <span style={{ display: 'block', fontSize: '0.8125rem', color: 'var(--color-text-secondary)', fontWeight: '400', marginTop: 'var(--space-1)' }}>
                  Pay in cash upon physical delivery of your order.
                </span>
              </label>
            </div>
          </div>

          {/* Section 4: Delivery Notes */}
          <div className="card checkout-section-card" style={{ marginTop: 'var(--space-6)' }}>
            <h2 className="card-title">Delivery Instructions (Optional)</h2>
            <div style={{ marginTop: 'var(--space-3)' }}>
              <textarea
                className="form-input"
                rows="3"
                placeholder="E.g. Landmark nearby, call upon arrival, leave with receptionist..."
                value={orderNotes}
                onChange={(e) => setOrderNotes(e.target.value)}
                maxLength={1000}
                style={{ width: '100%', resize: 'vertical' }}
              />
            </div>
          </div>
        </div>

        {/* Right Column: Order Summary Sidebar */}
        <div className="checkout-sidebar">
          <div className="card cart-summary-card">
            <h2 className="cart-summary-title">Order Summary</h2>

            <div className="cart-summary-breakdown">
              <div className="summary-row">
                <span className="summary-label">Subtotal</span>
                <span className="summary-val summary-subtotal">{authoritativeSubtotal}</span>
              </div>

              <div className="summary-row">
                <span className="summary-label">Shipping</span>
                <span className="summary-val">
                  {validationResult?.shipping_fee === '0.00' || validationResult?.shipping_fee === 0
                    ? 'Free'
                    : authoritativeShipping}
                </span>
              </div>

              <div className="summary-row">
                <span className="summary-label">Estimated Tax</span>
                <span className="summary-val">$0.00</span>
              </div>
            </div>

            <div className="cart-summary-total-divider" />

            <div className="summary-row summary-total-row">
              <span className="summary-total-label">Total</span>
              <span className="summary-total-val">{authoritativeTotal}</span>
            </div>

            <div className="cart-checkout-box">
              {placeOrderError && (
                <div className="alert alert-danger" style={{ marginBottom: 'var(--space-3)' }}>
                  <span>{placeOrderError}</span>
                </div>
              )}

              <button
                type="button"
                className="btn btn-primary btn-block"
                onClick={handlePlaceOrder}
                disabled={validating || placingOrder || !selectedAddress || hasIssues || !validationSuccess}
              >
                {placingOrder
                  ? 'Placing Order...'
                  : validating
                  ? 'Verifying Cart...'
                  : 'Place Order (Cash on Delivery)'}
              </button>

              <p className="checkout-helper-note">
                Orders are confirmed upon submission. Payment is collected in cash upon delivery.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CheckoutPage;
