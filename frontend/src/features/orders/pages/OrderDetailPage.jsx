import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import orderService from '../services/orderService';
import { OrderStatusBadge } from '../components';
import { PaymentSummaryCard, paymentService } from '../../payment';

export const OrderDetailPage = () => {
  const { orderNumber } = useParams();

  const [order, setOrder] = useState(null);
  const [payment, setPayment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [actionSuccess, setActionSuccess] = useState('');

  const fetchOrderDetail = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await orderService.getMyOrderDetail(orderNumber);
      setOrder(data);
      if (data.payment) {
        setPayment(data.payment);
      } else {
        try {
          const payData = await paymentService.getOrderPayment(orderNumber);
          setPayment(payData);
        } catch {
          // Non-blocking if payment endpoint not yet available
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load order details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrderDetail();
  }, [orderNumber]);

  const handleCancelOrder = async () => {
    setCancelling(true);
    setError('');
    try {
      const updated = await orderService.cancelMyOrder(orderNumber);
      setOrder(updated);
      setActionSuccess('Your order has been successfully cancelled.');
      setCancelModalOpen(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to cancel order.');
    } finally {
      setCancelling(false);
    }
  };

  const isCancellable =
    order && (order.status === 'PENDING' || order.status === 'CONFIRMED');


  if (loading) {
    return (
      <div className="container page-wrapper">
        <div style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
          <p>Loading order details...</p>
        </div>
      </div>
    );
  }

  if (error && !order) {
    return (
      <div className="container page-wrapper">
        <div className="card" style={{ textAlign: 'center', padding: 'var(--space-8)' }}>
          <h2 style={{ color: 'var(--color-danger)', marginBottom: 'var(--space-2)' }}>
            Order Not Found
          </h2>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-6)' }}>
            {error}
          </p>
          <Link to="/orders" className="btn btn-primary">
            ← Back to Orders
          </Link>
        </div>
      </div>
    );
  }

  const formattedSubtotal = Number(order.subtotal).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });
  const formattedShipping = Number(order.shipping_fee).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });
  const formattedTotal = Number(order.total_amount).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });
  const formattedDate = new Date(order.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="container page-wrapper">
      <div className="order-detail-header-bar">
        <div>
          <Link to="/orders" className="back-link">
            ← Back to Orders
          </Link>
          <h1 className="page-title" style={{ marginTop: 'var(--space-2)' }}>
            Order #{order.order_number}
          </h1>
          <p className="page-subtitle">Placed on {formattedDate}</p>
        </div>

        <div className="order-detail-header-actions">
          <OrderStatusBadge status={order.status} />
          <span className="badge badge-info">
            Payment: {order.payment_method} ({order.payment_status})
          </span>
          {isCancellable && (
            <button
              type="button"
              className="btn btn-danger btn-sm"
              onClick={() => setCancelModalOpen(true)}
            >
              Cancel Order
            </button>
          )}
        </div>
      </div>

      {actionSuccess && (
        <div className="alert alert-success" style={{ marginBottom: 'var(--space-6)' }}>
          <span>{actionSuccess}</span>
        </div>
      )}

      {error && (
        <div className="alert alert-danger" style={{ marginBottom: 'var(--space-6)' }}>
          <span>{error}</span>
        </div>
      )}

      {order.status === 'CANCELLED' && (
        <div className="alert alert-warning" style={{ marginBottom: 'var(--space-6)' }}>
          <span>
            This order was cancelled{order.cancelled_at ? ` on ${new Date(order.cancelled_at).toLocaleString('en-US')}` : ''}. Stock quantities have been restored.
          </span>
        </div>
      )}

      <div className="order-detail-grid">
        {/* Left / Main Column: Items Table & Totals */}
        <div className="order-detail-main">
          <div className="card">
            <h2 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>
              Ordered Items ({order.items.length})
            </h2>

            <div className="order-items-table">
              <div className="order-items-head">
                <span style={{ flex: 3 }}>Item</span>
                <span style={{ flex: 1, textAlign: 'center' }}>SKU</span>
                <span style={{ flex: 1, textAlign: 'right' }}>Price</span>
                <span style={{ flex: 1, textAlign: 'center' }}>Qty</span>
                <span style={{ flex: 1, textAlign: 'right' }}>Total</span>
              </div>

              {order.items.map((item) => (
                <div key={item.id} className="order-items-row">
                  <div style={{ flex: 3 }}>
                    <span className="order-item-title">{item.product_name}</span>
                  </div>
                  <div style={{ flex: 1, textAlign: 'center', fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                    {item.product_sku}
                  </div>
                  <div style={{ flex: 1, textAlign: 'right', fontSize: '0.875rem' }}>
                    {Number(item.unit_price).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                  </div>
                  <div style={{ flex: 1, textAlign: 'center', fontSize: '0.875rem' }}>
                    {item.quantity}
                  </div>
                  <div style={{ flex: 1, textAlign: 'right', fontWeight: 600 }}>
                    {Number(item.subtotal).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                  </div>
                </div>
              ))}
            </div>

            <div className="cart-summary-total-divider"></div>

            <div className="order-totals-summary">
              <div className="summary-row">
                <span className="summary-label">Subtotal</span>
                <span className="summary-val">{formattedSubtotal}</span>
              </div>
              <div className="summary-row">
                <span className="summary-label">Shipping</span>
                <span className="summary-val">{formattedShipping}</span>
              </div>
              <div className="cart-summary-total-divider"></div>
              <div className="summary-row summary-total-row">
                <span className="summary-total-label">Total Paid / Due</span>
                <span className="summary-total-val">{formattedTotal}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Customer & Delivery Info */}
        <div className="order-detail-side">
          <div className="card">
            <h2 className="card-title" style={{ marginBottom: 'var(--space-3)' }}>
              Delivery Address
            </h2>
            <div style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--color-text-secondary)' }}>
              <p>
                <strong style={{ color: 'var(--color-text)' }}>{order.recipient_name || order.customer_name}</strong>
              </p>
              <p>{order.shipping_address_line1}</p>
              {order.shipping_address_line2 && <p>{order.shipping_address_line2}</p>}
              {order.shipping_barangay && <p>Brgy. {order.shipping_barangay}</p>}
              <p>
                {order.shipping_city}, {order.shipping_province} {order.shipping_postal_code}
              </p>
              <p>{order.shipping_country}</p>
            </div>

            {order.notes && (
              <>
                <div className="cart-summary-total-divider" style={{ margin: 'var(--space-4) 0' }}></div>
                <h2 className="card-title" style={{ marginBottom: 'var(--space-2)' }}>
                  Delivery Notes
                </h2>
                <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
                  "{order.notes}"
                </p>
              </>
            )}

            <div className="cart-summary-total-divider" style={{ margin: 'var(--space-4) 0' }}></div>

            <h2 className="card-title" style={{ marginBottom: 'var(--space-3)' }}>
              Contact Information
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

            <PaymentSummaryCard payment={payment || order.payment} />
          </div>
        </div>
      </div>

      {/* Cancellation Confirmation Modal */}
      {cancelModalOpen && (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal-content card">
            <h2 className="card-title" style={{ marginBottom: 'var(--space-3)', color: 'var(--color-danger)' }}>
              Confirm Order Cancellation
            </h2>
            <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-4)', lineHeight: 1.5 }}>
              Are you sure you want to cancel order <strong>#{order.order_number}</strong>?
              This action cannot be undone. Allocated inventory units will be immediately released.
            </p>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button
                type="button"
                className="btn btn-outline"
                disabled={cancelling}
                onClick={() => setCancelModalOpen(false)}
              >
                Keep Order
              </button>
              <button
                type="button"
                className="btn btn-danger"
                disabled={cancelling}
                onClick={handleCancelOrder}
              >
                {cancelling ? 'Cancelling...' : 'Yes, Cancel Order'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderDetailPage;
