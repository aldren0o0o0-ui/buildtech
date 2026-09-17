import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import orderService from '../services/orderService';
import { OrderStatusBadge, OrderEmpty } from '../components';

export const OrdersPage = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const fetchOrders = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await orderService.getMyOrders(page, 10, statusFilter || null);
      setOrders(data.items || []);
      setTotalPages(data.pages || 1);
      setTotalCount(data.total || 0);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load your order history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [page, statusFilter]);

  const handleStatusTab = (status) => {
    setStatusFilter(status);
    setPage(1);
  };


  return (
    <div className="container page-wrapper">
      <div className="orders-page-header">
        <h1 className="page-title">My Orders</h1>
        <p className="page-subtitle">View and track your previous component orders and purchases.</p>
      </div>

      {/* Filter Tabs */}
      <div className="order-filter-tabs">
        {[
          { label: 'All Orders', value: '' },
          { label: 'Confirmed', value: 'CONFIRMED' },
          { label: 'Processing', value: 'PROCESSING' },
          { label: 'Shipped', value: 'SHIPPED' },
          { label: 'Delivered', value: 'DELIVERED' },
          { label: 'Cancelled', value: 'CANCELLED' },
        ].map((tab) => (
          <button
            key={tab.value}
            type="button"
            className={`filter-tab-btn ${statusFilter === tab.value ? 'active' : ''}`}
            onClick={() => handleStatusTab(tab.value)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="alert alert-danger" style={{ marginBottom: 'var(--space-6)' }}>
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
          <p>Loading your orders...</p>
        </div>
      ) : orders.length === 0 ? (
        <OrderEmpty statusFilter={statusFilter} />
      ) : (
        <div className="orders-list">
          {orders.map((order) => {
            const itemCount = order.items?.reduce((sum, i) => sum + i.quantity, 0) || 0;
            const formattedTotal = Number(order.total_amount).toLocaleString('en-US', {
              style: 'currency',
              currency: 'USD',
            });
            const createdDate = new Date(order.created_at).toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            });

            return (
              <div key={order.id} className="card order-card">
                <div className="order-card-header">
                  <div>
                    <span className="order-card-num">#{order.order_number}</span>
                    <span className="order-card-date">Placed on {createdDate}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                    <OrderStatusBadge status={order.status} />
                    <span className="badge badge-info">
                      {order.payment_method} ({order.payment_status})
                    </span>
                  </div>
                </div>

                <div className="order-card-body">
                  <div className="order-card-preview-items">
                    {order.items?.slice(0, 3).map((item) => (
                      <div key={item.id} className="order-preview-item">
                        <span className="order-preview-name">{item.product_name}</span>
                        <span className="order-preview-qty">×{item.quantity}</span>
                      </div>
                    ))}
                    {order.items?.length > 3 && (
                      <span style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                        + {order.items.length - 3} more item(s)
                      </span>
                    )}
                  </div>

                  <div className="order-card-summary">
                    <span className="order-card-items-count">
                      {itemCount} {itemCount === 1 ? 'item' : 'items'}
                    </span>
                    <span className="order-card-total">{formattedTotal}</span>
                  </div>
                </div>

                <div className="order-card-footer">
                  <Link
                    to={`/orders/${order.order_number}`}
                    className="btn btn-outline btn-sm"
                  >
                    View Order Details →
                  </Link>
                </div>
              </div>
            );
          })}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination-bar">
              <button
                type="button"
                className="btn btn-outline btn-sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                ← Previous
              </button>
              <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                Page {page} of {totalPages} ({totalCount} total orders)
              </span>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              >
                Next →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default OrdersPage;
