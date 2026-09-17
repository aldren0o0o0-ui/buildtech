import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import orderService from '../services/orderService';
import { OrderStatusBadge } from '../components';
import { AdminNav } from '../../admin';

export const AdminOrdersPage = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [paymentFilter, setPaymentFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalOrders, setTotalOrders] = useState(0);

  const fetchAdminOrders = async () => {
    setLoading(true);
    setError('');
    try {
      const params = {
        page,
        page_size: 10,
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        payment_status: paymentFilter || undefined,
      };
      const data = await orderService.getAdminOrders(params);
      setOrders(data.items || []);
      setTotalPages(data.pages || 1);
      setTotalOrders(data.total || 0);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch admin orders.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminOrders();
  }, [page, statusFilter, paymentFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchAdminOrders();
  };


  return (
    <>
      <AdminNav activeTitle="Orders Management" />
      <div className="container page-wrapper" style={{ paddingTop: 0 }}>
        <div className="admin-orders-header">
          <div>
            <h1 className="page-title">
              Orders Management
            </h1>
            <p className="page-subtitle">Review, search, and manage customer orders and workflow transitions.</p>
          </div>
        </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ marginBottom: 'var(--space-6)', padding: 'var(--space-4)' }}>
        <form onSubmit={handleSearchSubmit} className="admin-filter-bar">
          <div style={{ flex: 2 }}>
            <input
              type="text"
              className="form-input"
              placeholder="Search by order #, customer name, or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div style={{ flex: 1 }}>
            <select
              className="form-input"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Order Statuses</option>
              <option value="PENDING">PENDING</option>
              <option value="CONFIRMED">CONFIRMED</option>
              <option value="PROCESSING">PROCESSING</option>
              <option value="SHIPPED">SHIPPED</option>
              <option value="DELIVERED">DELIVERED</option>
              <option value="READY_FOR_FULFILLMENT">READY_FOR_FULFILLMENT</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>

          <div style={{ flex: 1 }}>
            <select
              className="form-input"
              value={paymentFilter}
              onChange={(e) => {
                setPaymentFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Payment Statuses</option>
              <option value="PENDING">PENDING</option>
              <option value="PAID">PAID</option>
              <option value="FAILED">FAILED</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>

          <button type="submit" className="btn btn-primary btn-sm">
            Search
          </button>
          {(search || statusFilter || paymentFilter) && (
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => {
                setSearch('');
                setStatusFilter('');
                setPaymentFilter('');
                setPage(1);
              }}
            >
              Reset
            </button>
          )}
        </form>
      </div>

      {error && (
        <div className="alert alert-danger" style={{ marginBottom: 'var(--space-6)' }}>
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
          <p>Loading orders...</p>
        </div>
      ) : orders.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 'var(--space-10)' }}>
          <h2 style={{ fontSize: '1.25rem', marginBottom: 'var(--space-2)' }}>No Orders Found</h2>
          <p style={{ color: 'var(--color-text-secondary)' }}>
            No customer orders matched the given search and filter criteria.
          </p>
        </div>
      ) : (
        <div className="card table-responsive-wrapper" style={{ padding: 0 }}>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Order #</th>
                <th>Customer</th>
                <th>Date</th>
                <th>Items</th>
                <th>Total</th>
                <th>Payment</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order) => {
                const totalUnits = order.items?.reduce((acc, i) => acc + i.quantity, 0) || 0;
                const dateStr = new Date(order.created_at).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                });
                return (
                  <tr key={order.id}>
                    <td>
                      <strong>#{order.order_number}</strong>
                    </td>
                    <td>
                      <div>
                        <div>{order.customer_name}</div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                          {order.customer_email}
                        </span>
                      </div>
                    </td>
                    <td style={{ fontSize: '0.875rem' }}>{dateStr}</td>
                    <td style={{ fontSize: '0.875rem' }}>
                      {totalUnits} {totalUnits === 1 ? 'unit' : 'units'}
                    </td>
                    <td style={{ fontWeight: 600 }}>
                      {Number(order.total_amount).toLocaleString('en-US', {
                        style: 'currency',
                        currency: 'USD',
                      })}
                    </td>
                    <td>
                      <span className="badge badge-info">
                        {order.payment_method} ({order.payment_status})
                      </span>
                    </td>
                    <td>
                      <OrderStatusBadge status={order.status} />
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <Link
                        to={`/admin/orders/${order.id}`}
                        className="btn btn-outline btn-sm"
                      >
                        Manage →
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="pagination-bar" style={{ padding: 'var(--space-4)' }}>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                ← Previous
              </button>
              <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                Page {page} of {totalPages} ({totalOrders} total orders)
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
    </>
  );
};

export default AdminOrdersPage;
