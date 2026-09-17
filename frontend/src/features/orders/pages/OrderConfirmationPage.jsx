import { useEffect, useState } from 'react';
import { useLocation, useParams, Link } from 'react-router-dom';
import orderService from '../services/orderService';

export const OrderConfirmationPage = () => {
  const { orderNumber } = useParams();
  const location = useLocation();

  const [order, setOrder] = useState(location.state?.order || null);
  const [loading, setLoading] = useState(!order);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!order && orderNumber) {
      const fetchOrder = async () => {
        try {
          const data = await orderService.getMyOrderDetail(orderNumber);
          setOrder(data);
        } catch (err) {
          setError(
            err.response?.data?.detail || 'Failed to retrieve order confirmation details.'
          );
        } finally {
          setLoading(false);
        }
      };
      fetchOrder();
    }
  }, [order, orderNumber]);

  if (loading) {
    return (
      <div className="container page-wrapper">
        <div style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
          <p>Loading order confirmation...</p>
        </div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="container page-wrapper">
        <div className="card" style={{ textAlign: 'center', padding: 'var(--space-8)' }}>
          <h2 style={{ color: 'var(--color-danger)', marginBottom: 'var(--space-3)' }}>
            Unable to Load Order
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-6)' }}>
            {error || 'Order record could not be found.'}
          </p>
          <Link to="/orders" className="btn btn-primary">
            View My Orders
          </Link>
        </div>
      </div>
    );
  }

  const formattedTotal = Number(order.total_amount).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });
  const formattedSubtotal = Number(order.subtotal).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });
  const formattedShipping = Number(order.shipping_fee).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });

  return (
    <div className="container page-wrapper">
      <div className="order-confirmation-container">
        {/* Success Header Banner */}
        <div className="confirmation-header-card">
          <div className="confirmation-badge-icon">
            <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
          <h1 className="confirmation-title">Order Confirmed</h1>
          <p className="confirmation-order-num">
            Order Number: <strong>#{order.order_number}</strong>
          </p>
          <p className="confirmation-msg">
            Thank you for your purchase. Your order has been placed and is being processed.
          </p>

          <div className="confirmation-status-pill-group">
            <span className="badge badge-success">Status: {order.status}</span>
            <span className="badge badge-info">
              Payment: {order.payment_method} ({order.payment_status})
            </span>
          </div>
        </div>

        {/* Order Details Grid */}
        <div className="confirmation-grid">
          {/* Purchased Items List */}
          <div className="card confirmation-items-card">
            <h2 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>
              Purchased Items ({order.items.length})
            </h2>

            <div className="confirmation-item-table">
              {order.items.map((item) => (
                <div key={item.id} className="confirmation-item-row">
                  <div className="confirmation-item-info">
                    <span className="confirmation-item-name">{item.product_name}</span>
                    <span className="confirmation-item-sku">SKU: {item.product_sku}</span>
                    <span className="confirmation-item-qty">
                      Quantity: {item.quantity} × {Number(item.unit_price).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                    </span>
                  </div>
                  <span className="confirmation-item-subtotal">
                    {Number(item.subtotal).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                  </span>
                </div>
              ))}
            </div>

            <div className="cart-summary-total-divider"></div>

            <div className="confirmation-totals-breakdown">
              <div className="summary-row">
                <span className="summary-label">Subtotal</span>
                <span className="summary-val">{formattedSubtotal}</span>
              </div>
              <div className="summary-row">
                <span className="summary-label">Shipping Fee</span>
                <span className="summary-val">{formattedShipping}</span>
              </div>
              <div className="cart-summary-total-divider"></div>
              <div className="summary-row summary-total-row">
                <span className="summary-total-label">Total Amount</span>
                <span className="summary-total-val">{formattedTotal}</span>
              </div>
            </div>
          </div>

          {/* Delivery & Customer Snapshot Info */}
          <div className="confirmation-side-col">
            <div className="card">
              <h2 className="card-title" style={{ marginBottom: 'var(--space-3)' }}>
                Delivery Information
              </h2>
              <div style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--color-text-secondary)' }}>
                <p>
                  Recipient: <strong style={{ color: 'var(--color-text)' }}>{order.recipient_name || order.customer_name}</strong>
                </p>
                <p>
                  Address:{' '}
                  <strong style={{ color: 'var(--color-text)' }}>
                    {order.shipping_address_line1}
                    {order.shipping_address_line2 ? `, ${order.shipping_address_line2}` : ''}
                    {order.shipping_barangay ? `, Brgy. ${order.shipping_barangay}` : ''}
                  </strong>
                </p>
                <p>
                  Location:{' '}
                  <strong style={{ color: 'var(--color-text)' }}>
                    {order.shipping_city}, {order.shipping_province} {order.shipping_postal_code}
                  </strong>
                </p>
                <p>
                  Country: <strong style={{ color: 'var(--color-text)' }}>{order.shipping_country}</strong>
                </p>
                {order.notes && (
                  <p style={{ marginTop: 'var(--space-2)' }}>
                    Notes: <strong style={{ color: 'var(--color-text)' }}>{order.notes}</strong>
                  </p>
                )}
              </div>

              <div className="cart-summary-total-divider" style={{ margin: 'var(--space-4) 0' }}></div>

              <h2 className="card-title" style={{ marginBottom: 'var(--space-3)' }}>
                Contact Details
              </h2>
              <div style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--color-text-secondary)' }}>
                <p>
                  Email: <strong style={{ color: 'var(--color-text)' }}>{order.customer_email}</strong>
                </p>
                <p>
                  Phone: <strong style={{ color: 'var(--color-text)' }}>{order.customer_phone}</strong>
                </p>
              </div>

              <div className="cart-summary-total-divider" style={{ margin: 'var(--space-4) 0' }}></div>

              <h2 className="card-title" style={{ marginBottom: 'var(--space-3)' }}>
                Payment Details
              </h2>
              <div style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--color-text-secondary)' }}>
                {order.payment?.payment_reference && (
                  <p>
                    Reference: <strong style={{ color: 'var(--color-text)' }}>{order.payment.payment_reference}</strong>
                  </p>
                )}
                <p>
                  Method: <strong>Cash on Delivery (COD)</strong>
                </p>
                <p>
                  Status:{' '}
                  <strong style={{ color: (order.payment?.status || order.payment_status) === 'PAID' ? 'var(--color-success)' : 'var(--color-warning)' }}>
                    {order.payment?.status || order.payment_status}
                  </strong>
                </p>
                <p style={{ marginTop: '0.25rem', fontSize: '0.8125rem' }}>
                  Please prepare exact cash amount of <strong style={{ color: 'var(--color-primary)' }}>{formattedTotal}</strong> upon parcel arrival.
                </p>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="confirmation-actions-box">
              <Link to="/orders" className="btn btn-primary btn-block">
                View All My Orders
              </Link>
              <Link to="/products" className="btn btn-outline btn-block">
                Continue Shopping
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderConfirmationPage;
