import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import orderService from '../services/orderService';
import { OrderStatusBadge } from '../components';
import { PaymentSummaryCard, paymentService } from '../../payment';
import { AdminNav } from '../../admin';

const ALLOWED_TRANSITIONS = {
  PENDING: ['CONFIRMED', 'CANCELLED'],
  CONFIRMED: ['PROCESSING', 'CANCELLED'],
  PROCESSING: ['SHIPPED', 'READY_FOR_FULFILLMENT', 'CANCELLED'],
  SHIPPED: ['DELIVERED'],
  READY_FOR_FULFILLMENT: ['COMPLETED', 'CANCELLED'],
  DELIVERED: [],
  COMPLETED: [],
  CANCELLED: [],
};

export const AdminOrderDetailPage = () => {
  const { orderId } = useParams();

  const [order, setOrder] = useState(null);
  const [payment, setPayment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [targetStatus, setTargetStatus] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [updateSuccess, setUpdateSuccess] = useState('');

  const fetchOrderDetail = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await orderService.getAdminOrderDetail(orderId);
      setOrder(data);
      if (data.payment) {
        setPayment(data.payment);
      } else {
        try {
          const payData = await paymentService.getOrderPayment(orderId);
          setPayment(payData);
        } catch {
          // Non-blocking if payment endpoint not yet available
        }
      }
      const nextAllowed = ALLOWED_TRANSITIONS[data.status] || [];
      setTargetStatus(nextAllowed[0] || '');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch order details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrderDetail();
  }, [orderId]);

  const handleStatusUpdate = async (e) => {
    e.preventDefault();
    if (!targetStatus) return;

    setUpdatingStatus(true);
    setError('');
    setUpdateSuccess('');

    try {
      const updated = await orderService.updateAdminOrderStatus(orderId, targetStatus);
      setOrder(updated);
      setUpdateSuccess(`Order status successfully updated to ${updated.status}.`);
      const nextAllowed = ALLOWED_TRANSITIONS[updated.status] || [];
      setTargetStatus(nextAllowed[0] || '');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to transition order status.');
    } finally {
      setUpdatingStatus(false);
    }
  };


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
          <Link to="/admin/orders" className="btn btn-primary">
            ← Back to Orders Management
          </Link>
        </div>
      </div>
    );
  }

  const allowedOptions = ALLOWED_TRANSITIONS[order.status] || [];
  const isTerminal = allowedOptions.length === 0;

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
  const formattedDate = new Date(order.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <>
      <AdminNav activeTitle={`Order #${order.order_number}`} />
      <div className="container page-wrapper" style={{ paddingTop: 0 }}>
        <div className="order-detail-header-bar">
          <div>
            <Link to="/admin/orders" className="back-link">
              ← Back to Orders Management
            </Link>
          <h1 className="page-title" style={{ marginTop: 'var(--space-2)' }}>
            Manage Order #{order.order_number}
          </h1>
          <p className="page-subtitle">Submitted on {formattedDate}</p>
        </div>

        <div className="admin-order-header-badges">
          <OrderStatusBadge status={order.status} />
          <span className="badge badge-info">
            Payment: {order.payment_method} ({order.payment_status})
          </span>
        </div>
      </div>

      {updateSuccess && (
        <div className="alert alert-success" style={{ marginBottom: 'var(--space-6)' }}>
          <span>{updateSuccess}</span>
        </div>
      )}

      {order.status === 'CANCELLED' && (
        <div className="alert alert-warning" style={{ marginBottom: 'var(--space-6)' }}>
          <span>
            This order has been CANCELLED{order.cancelled_at ? ` on ${new Date(order.cancelled_at).toLocaleString('en-US')}` : ''}. Inventory stock has been restored to available quantities.
          </span>
        </div>
      )}

      {error && (
        <div className="alert alert-danger" style={{ marginBottom: 'var(--space-6)' }}>
          <span>{error}</span>
        </div>
      )}

      {/* Status Transition Control Card */}
      <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
        <h2 className="card-title" style={{ marginBottom: 'var(--space-3)' }}>
          Order Workflow & Status Transition
        </h2>

        {isTerminal ? (
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
            This order is in a terminal status (<strong>{order.status}</strong>). No further transitions are permitted.
          </p>
        ) : (
          <form onSubmit={handleStatusUpdate} style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ minWidth: '220px' }}>
              <label htmlFor="target_status" className="form-label" style={{ marginBottom: '0.25rem' }}>
                Transition To:
              </label>
              <select
                id="target_status"
                className="form-input"
                value={targetStatus}
                onChange={(e) => setTargetStatus(e.target.value)}
                disabled={updatingStatus}
              >
                {allowedOptions.map((statusOpt) => (
                  <option key={statusOpt} value={statusOpt}>
                    {statusOpt}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ alignSelf: 'flex-end' }}>
              <button
                type="submit"
                className={`btn ${targetStatus === 'CANCELLED' ? 'btn-danger' : 'btn-primary'}`}
                disabled={updatingStatus || !targetStatus}
              >
                {updatingStatus ? 'Updating...' : `Apply Transition (${targetStatus})`}
              </button>
            </div>

            {targetStatus === 'CANCELLED' && (
              <span style={{ fontSize: '0.8125rem', color: 'var(--color-danger)', width: '100%' }}>
                Warning: Transitioning to CANCELLED will automatically restore allocated product inventory.
              </span>
            )}
          </form>
        )}
      </div>

      <div className="order-detail-grid">
        {/* Left Column: Items Table & Totals */}
        <div className="order-detail-main">
          <div className="card">
            <h2 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>
              Ordered Items Snapshot ({order.items.length})
            </h2>

            <div className="order-items-table">
              <div className="order-items-head">
                <span style={{ flex: 3 }}>Item</span>
                <span style={{ flex: 1, textAlign: 'center' }}>SKU</span>
                <span style={{ flex: 1, textAlign: 'right' }}>Unit Price</span>
                <span style={{ flex: 1, textAlign: 'center' }}>Quantity</span>
                <span style={{ flex: 1, textAlign: 'right' }}>Subtotal</span>
              </div>

              {order.items.map((item) => (
                <div key={item.id} className="order-items-row">
                  <div style={{ flex: 3 }}>
                    <span className="order-item-title">{item.product_name}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', display: 'block' }}>
                      Slug: {item.product_slug}
                    </span>
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
                <span className="summary-total-label">Total Amount</span>
                <span className="summary-total-val">{formattedTotal}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Customer & Delivery Information */}
        <div className="order-detail-side">
          <div className="card">
            <h2 className="card-title" style={{ marginBottom: 'var(--space-3)' }}>
              Customer Information
            </h2>
            <div style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--color-text-secondary)' }}>
              <p>
                Name: <strong style={{ color: 'var(--color-text)' }}>{order.customer_name}</strong>
              </p>
              <p>
                Email: <strong style={{ color: 'var(--color-text)' }}>{order.customer_email}</strong>
              </p>
              <p>
                Phone: <strong style={{ color: 'var(--color-text)' }}>{order.customer_phone}</strong>
              </p>
              {order.user_id && (
                <p>
                  User Account ID: <strong style={{ color: 'var(--color-text)' }}>#{order.user_id}</strong>
                </p>
              )}
            </div>

            <div className="cart-summary-total-divider" style={{ margin: 'var(--space-4) 0' }}></div>

            <h2 className="card-title" style={{ marginBottom: 'var(--space-3)' }}>
              Shipping Address
            </h2>
            <div style={{ fontSize: '0.875rem', lineHeight: 1.6, color: 'var(--color-text-secondary)' }}>
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
                  Customer Notes
                </h2>
                <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', fontStyle: 'italic' }}>
                  "{order.notes}"
                </p>
              </>
            )}

            <div className="cart-summary-total-divider" style={{ margin: 'var(--space-4) 0' }}></div>

            <PaymentSummaryCard
              payment={payment || order.payment}
              isAdmin={true}
              onPaymentUpdated={(updated) => {
                setPayment(updated);
                setOrder((prev) =>
                  prev
                    ? {
                        ...prev,
                        payment_status: updated.status,
                        payment: updated,
                      }
                    : prev
                );
              }}
            />
          </div>
        </div>
      </div>
      </div>
    </>
  );
};

export default AdminOrderDetailPage;
