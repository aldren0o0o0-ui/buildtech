import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';
import adminDashboardService from '../services/adminDashboardService';
import AdminNav from '../components/AdminNav';

export const AdminDashboardPage = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = useCallback(async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError('');

    try {
      const res = await adminDashboardService.getDashboardData();
      setData(res);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Failed to retrieve operational dashboard data. Please verify network connection and server status.'
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const formatCurrency = (amount) => {
    const val = parseFloat(amount || 0);
    return new Intl.NumberFormat('en-PH', {
      style: 'currency',
      currency: 'PHP',
      minimumFractionDigits: 2,
    }).format(val);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    try {
      const d = new Date(dateString);
      return d.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  const getOrderStatusBadgeClass = (status) => {
    switch (status) {
      case 'DELIVERED':
      case 'COMPLETED':
        return 'badge-success';
      case 'CONFIRMED':
      case 'PROCESSING':
        return 'badge-primary';
      case 'READY_FOR_FULFILLMENT':
      case 'SHIPPED':
        return 'badge-info';
      case 'PENDING':
        return 'badge-warning';
      case 'CANCELLED':
        return 'badge-danger';
      default:
        return 'badge-secondary';
    }
  };

  const getPaymentStatusBadgeClass = (status) => {
    switch (status) {
      case 'PAID':
        return 'badge-success';
      case 'PENDING':
        return 'badge-warning';
      case 'FAILED':
      case 'CANCELLED':
        return 'badge-danger';
      default:
        return 'badge-secondary';
    }
  };

  return (
    <>
      <AdminNav activeTitle="Operational Dashboard" />
      <div className="container page-wrapper" style={{ paddingTop: 0 }}>
      {/* Dashboard Operational Header */}
      <div
        className="page-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          flexWrap: 'wrap',
          gap: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <h1 className="page-title" style={{ margin: 0 }}>
              Admin Dashboard
            </h1>
            <span
              className="badge badge-admin"
              style={{ padding: '4px 10px', fontSize: '0.8rem', fontWeight: 600 }}
            >
              OPERATIONAL
            </span>
          </div>
          <p
            className="page-subtitle"
            style={{ margin: 'var(--space-1) 0 0 0', color: 'var(--color-text-secondary)' }}
          >
            Real-time financial overview, order lifecycle tracking, inventory health, and catalog activity.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => fetchDashboardData(true)}
            disabled={loading || refreshing}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <svg
              viewBox="0 0 24 24"
              width="14"
              height="14"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }}
              aria-hidden="true"
            >
              <polyline points="23 4 23 10 17 10" />
              <polyline points="1 20 1 14 7 14" />
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
            </svg>
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
          <div
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              background: 'var(--color-bg-secondary, rgba(255,255,255,0.04))',
              border: '1px solid var(--color-border-subtle, rgba(255,255,255,0.08))',
              fontSize: '0.825rem',
              color: 'var(--color-text-secondary)',
            }}
          >
            Admin: <strong style={{ color: 'var(--color-text-primary, #f3f4f6)' }}>{user?.email}</strong>
          </div>
        </div>
      </div>

      {/* Error Alert State */}
      {error && (
        <div
          className="card"
          style={{
            padding: 'var(--space-6)',
            marginBottom: 'var(--space-6)',
            borderLeft: '4px solid var(--color-danger, #ef4444)',
            background: 'rgba(239, 68, 68, 0.08)',
          }}
        >
          <h3 style={{ margin: '0 0 var(--space-2)', color: '#f87171' }}>Unable to load dashboard data</h3>
          <p style={{ margin: '0 0 var(--space-4)', color: 'var(--color-text-secondary)' }}>{error}</p>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => fetchDashboardData(false)}
          >
            Try Again
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && !data && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          {/* KPI Skeleton */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: 'var(--space-4)',
            }}
          >
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="card" style={{ padding: 'var(--space-6)', minHeight: '120px' }}>
                <div style={{ height: '16px', width: '40%', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', marginBottom: '12px' }} />
                <div style={{ height: '32px', width: '70%', background: 'rgba(255,255,255,0.1)', borderRadius: '6px', marginBottom: '8px' }} />
                <div style={{ height: '14px', width: '50%', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }} />
              </div>
            ))}
          </div>

          <div style={{ textAlign: 'center', padding: 'var(--space-8)' }}>
            <div className="spinner" style={{ margin: '0 auto var(--space-2)' }} />
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
              Aggregating live operational metrics...
            </p>
          </div>
        </div>
      )}

      {/* Loaded Dashboard Content */}
      {data && (
        <>
          {/* 1. Primary KPI Stat Cards Grid (4 Columns) */}
          <div
            className="dashboard-kpi-grid"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: 'var(--space-4)',
              marginBottom: 'var(--space-6)',
            }}
          >
            {/* Total Paid Revenue */}
            <div className="card kpi-card" style={{ padding: 'var(--space-5)', margin: 0 }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 'var(--space-2)' }}>
                Paid Revenue
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-text)', lineHeight: 1.2 }}>
                {formatCurrency(data.overview.total_revenue)}
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 'var(--space-2)' }}>
                Pending: {formatCurrency(data.overview.pending_payment)}
              </div>
            </div>

            {/* Total Orders */}
            <div className="card kpi-card" style={{ padding: 'var(--space-5)', margin: 0 }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 'var(--space-2)' }}>
                Total Orders
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-text)', lineHeight: 1.2 }}>
                {data.overview.total_orders}
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 'var(--space-2)' }}>
                Gross: {formatCurrency(data.overview.total_order_value)}
              </div>
            </div>

            {/* Registered Customers */}
            <div className="card kpi-card" style={{ padding: 'var(--space-5)', margin: 0 }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 'var(--space-2)' }}>
                Customers
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-text)', lineHeight: 1.2 }}>
                {data.overview.total_customers}
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 'var(--space-2)' }}>
                Active Accounts: {data.overview.active_customers}
              </div>
            </div>

            {/* Catalog Products */}
            <div className="card kpi-card" style={{ padding: 'var(--space-5)', margin: 0 }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 'var(--space-2)' }}>
                Hardware Catalog
              </div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-text)', lineHeight: 1.2 }}>
                {data.overview.total_products}
              </div>
              <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)', marginTop: 'var(--space-2)' }}>
                Active: {data.overview.active_products}
              </div>
            </div>
          </div>

          {/* 2. Middle Row: Order Lifecycle Breakdown & Low Stock Alerts */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
              gap: 'var(--space-6)',
              marginBottom: 'var(--space-6)',
            }}
          >
            {/* Order Lifecycle Breakdown */}
            <div className="card" style={{ padding: 'var(--space-6)', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
                <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700 }}>
                  Order Lifecycle Breakdown
                </h3>
                <Link to="/admin/orders" className="btn btn-outline btn-sm">
                  View Orders
                </Link>
              </div>

              <p style={{ margin: '0 0 var(--space-4)', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                Summary of customer orders partitioned by fulfillment stage.
              </p>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, 1fr)',
                  gap: 'var(--space-3)',
                  flex: 1,
                }}
              >
                {[
                  { label: 'Pending', count: data.orders_by_status.pending },
                  { label: 'Confirmed', count: data.orders_by_status.confirmed },
                  { label: 'Processing', count: data.orders_by_status.processing },
                  { label: 'Shipped', count: data.orders_by_status.shipped },
                  { label: 'Delivered', count: data.orders_by_status.delivered },
                  { label: 'Cancelled', count: data.orders_by_status.cancelled },
                ].map((s) => (
                  <div
                    key={s.label}
                    style={{
                      padding: 'var(--space-3)',
                      borderRadius: 'var(--radius-sm)',
                      background: 'var(--color-surface-muted)',
                      border: '1px solid var(--color-border-subtle)',
                    }}
                  >
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      {s.label}
                    </div>
                    <div style={{ fontSize: '1.35rem', fontWeight: 700, color: 'var(--color-text)', marginTop: 'var(--space-1)' }}>
                      {s.count}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Low Stock Alerts */}
            <div className="card" style={{ padding: 'var(--space-6)', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700 }}>
                    Low Stock Alerts
                  </h3>
                  {data.low_stock_products.length > 0 && (
                    <span className="badge badge-warning" style={{ fontSize: '0.75rem' }}>
                      {data.low_stock_products.length} need attention
                    </span>
                  )}
                </div>
                <Link to="/admin/inventory" className="btn btn-outline btn-sm">
                  Restock
                </Link>
              </div>

              {data.low_stock_products.length === 0 ? (
                <div
                  style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    textAlign: 'center',
                    padding: 'var(--space-6)',
                    background: 'var(--color-surface-muted)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px dashed var(--color-border-subtle)',
                  }}
                >
                  <h4 style={{ margin: '0 0 4px', color: 'var(--color-text)', fontSize: '0.9375rem', fontWeight: 600 }}>Inventory Healthy</h4>
                  <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                    No hardware components currently require restocking.
                  </p>
                </div>
              ) : (
                <div style={{ overflowX: 'auto', flex: 1 }}>
                  <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--color-border-subtle, rgba(255,255,255,0.08))' }}>
                        <th style={{ padding: '8px 6px' }}>Component</th>
                        <th style={{ padding: '8px 6px' }}>Available</th>
                        <th style={{ padding: '8px 6px' }}>Threshold</th>
                        <th style={{ padding: '8px 6px', textAlign: 'right' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.low_stock_products.slice(0, 5).map((item) => (
                        <tr key={item.product_id} style={{ borderBottom: '1px solid var(--color-border-subtle, rgba(255,255,255,0.04))' }}>
                          <td style={{ padding: '8px 6px' }}>
                            <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{item.name}</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>{item.sku}</div>
                          </td>
                          <td style={{ padding: '8px 6px', fontWeight: 700, color: item.available_quantity === 0 ? '#ef4444' : '#f59e0b' }}>
                            {item.available_quantity}
                          </td>
                          <td style={{ padding: '8px 6px', color: 'var(--color-text-secondary)' }}>
                            {item.low_stock_threshold}
                          </td>
                          <td style={{ padding: '8px 6px', textAlign: 'right' }}>
                            <span
                              className={`badge ${item.availability_status === 'OUT_OF_STOCK' ? 'badge-danger' : 'badge-warning'}`}
                              style={{ fontSize: '0.7rem', padding: '2px 6px' }}
                            >
                              {item.availability_status === 'OUT_OF_STOCK' ? 'OUT OF STOCK' : 'LOW STOCK'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* 3. Bottom Row: Top-Selling Products & Recent Orders */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
              gap: 'var(--space-6)',
              marginBottom: 'var(--space-8)',
            }}
          >
            {/* Top-Selling Products */}
            <div className="card" style={{ padding: 'var(--space-6)', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
                <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700 }}>
                  Top-Selling Components
                </h3>
                <Link to="/admin/products" className="btn btn-outline btn-sm">
                  View Catalog
                </Link>
              </div>

              {data.top_selling_products.length === 0 ? (
                <div
                  style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    textAlign: 'center',
                    padding: 'var(--space-6)',
                    background: 'var(--color-surface-muted)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px dashed var(--color-border-subtle)',
                  }}
                >
                  <h4 style={{ margin: '0 0 4px', fontSize: '0.9375rem', fontWeight: 600, color: 'var(--color-text)' }}>No Sales Data</h4>
                  <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                    Top-selling products will appear after confirmed customer purchases.
                  </p>
                </div>
              ) : (
                <div style={{ overflowX: 'auto', flex: 1 }}>
                  <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--color-border-subtle, rgba(255,255,255,0.08))' }}>
                        <th style={{ padding: '8px 6px' }}>Hardware Item</th>
                        <th style={{ padding: '8px 6px' }}>Units Sold</th>
                        <th style={{ padding: '8px 6px', textAlign: 'right' }}>Total Volume</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.top_selling_products.map((item, idx) => (
                        <tr key={item.product_id} style={{ borderBottom: '1px solid var(--color-border-subtle, rgba(255,255,255,0.04))' }}>
                          <td style={{ padding: '8px 6px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-primary, #6366f1)', minWidth: '16px' }}>
                                #{idx + 1}
                              </span>
                              <div>
                                <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{item.product_name}</div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>{item.product_sku}</div>
                              </div>
                            </div>
                          </td>
                          <td style={{ padding: '8px 6px', fontWeight: 700 }}>
                            {item.units_sold}
                          </td>
                          <td style={{ padding: '8px 6px', textAlign: 'right', fontWeight: 600, color: '#10b981' }}>
                            {formatCurrency(item.total_sales)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Recent Orders */}
            <div className="card" style={{ padding: 'var(--space-6)', display: 'flex', flexDirection: 'column' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
                <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700 }}>
                  Recent Orders
                </h3>
                <Link to="/admin/orders" className="btn btn-outline btn-sm">
                  View All
                </Link>
              </div>

              {data.recent_orders.length === 0 ? (
                <div
                  style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    textAlign: 'center',
                    padding: 'var(--space-6)',
                    background: 'var(--color-surface-muted)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px dashed var(--color-border-subtle)',
                  }}
                >
                  <h4 style={{ margin: '0 0 4px', fontSize: '0.9375rem', fontWeight: 600, color: 'var(--color-text)' }}>No Orders Yet</h4>
                  <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                    Customer orders will be logged here as they are placed.
                  </p>
                </div>
              ) : (
                <div style={{ overflowX: 'auto', flex: 1 }}>
                  <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--color-border-subtle, rgba(255,255,255,0.08))' }}>
                        <th style={{ padding: '8px 6px' }}>Order</th>
                        <th style={{ padding: '8px 6px' }}>Customer</th>
                        <th style={{ padding: '8px 6px' }}>Amount</th>
                        <th style={{ padding: '8px 6px' }}>Payment</th>
                        <th style={{ padding: '8px 6px', textAlign: 'right' }}>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recent_orders.slice(0, 6).map((o) => (
                        <tr key={o.id} style={{ borderBottom: '1px solid var(--color-border-subtle, rgba(255,255,255,0.04))' }}>
                          <td style={{ padding: '8px 6px' }}>
                            <Link
                              to={`/admin/orders/${o.id}`}
                              style={{ color: 'var(--color-primary, #6366f1)', textDecoration: 'none', fontWeight: 600 }}
                            >
                              {o.order_number}
                            </Link>
                            <div style={{ fontSize: '0.725rem', color: 'var(--color-text-secondary)' }}>
                              {formatDate(o.created_at)}
                            </div>
                          </td>
                          <td style={{ padding: '8px 6px' }}>
                            <div style={{ fontWeight: 500 }}>{o.customer_name}</div>
                          </td>
                          <td style={{ padding: '8px 6px', fontWeight: 600 }}>
                            {formatCurrency(o.total_amount)}
                          </td>
                          <td style={{ padding: '8px 6px' }}>
                            <span className={`badge ${getPaymentStatusBadgeClass(o.payment_status)}`} style={{ fontSize: '0.7rem', padding: '2px 6px' }}>
                              {o.payment_status}
                            </span>
                          </td>
                          <td style={{ padding: '8px 6px', textAlign: 'right' }}>
                            <span className={`badge ${getOrderStatusBadgeClass(o.status)}`} style={{ fontSize: '0.7rem', padding: '2px 6px' }}>
                              {o.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* 4. Module Management Quick Links Navigation Grid */}
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: 'var(--space-3)' }}>
              Management Modules
            </h3>
            <div className="admin-menu-grid">
              <Link to="/admin/orders" className="admin-menu-card">
                <div>
                  <h2 className="admin-menu-title">Orders Management</h2>
                  <p className="admin-menu-desc">
                    Process shipments, fulfill customer purchases, handle status transitions, and audit payments.
                  </p>
                </div>
                <span className="admin-menu-link-text">
                  Manage Orders
                </span>
              </Link>

              <Link to="/admin/inventory" className="admin-menu-card">
                <div>
                  <h2 className="admin-menu-title">Inventory Management</h2>
                  <p className="admin-menu-desc">
                    Track stock levels, replenish warehouse inventory, perform audits, and configure thresholds.
                  </p>
                </div>
                <span className="admin-menu-link-text">
                  Manage Inventory
                </span>
              </Link>

              <Link to="/admin/products" className="admin-menu-card">
                <div>
                  <h2 className="admin-menu-title">Products Catalog</h2>
                  <p className="admin-menu-desc">
                    Configure hardware components, SKUs, pricing, technical specifications, and publication states.
                  </p>
                </div>
                <span className="admin-menu-link-text">
                  Manage Products
                </span>
              </Link>

              <Link to="/admin/categories" className="admin-menu-card">
                <div>
                  <h2 className="admin-menu-title">Categories Management</h2>
                  <p className="admin-menu-desc">
                    Organize hardware taxonomies including CPUs, GPUs, Motherboards, Memory, and PSUs.
                  </p>
                </div>
                <span className="admin-menu-link-text">
                  Manage Categories
                </span>
              </Link>

              <Link to="/admin/brands" className="admin-menu-card">
                <div>
                  <h2 className="admin-menu-title">Brands Management</h2>
                  <p className="admin-menu-desc">
                    Manage manufacturers including NVIDIA, AMD, Intel, Corsair, ASUS, and MSI.
                  </p>
                </div>
                <span className="admin-menu-link-text">
                  Manage Brands
                </span>
              </Link>

              <Link to="/admin/reviews" className="admin-menu-card">
                <div>
                  <h2 className="admin-menu-title">Reviews Moderation</h2>
                  <p className="admin-menu-desc">
                    Moderate verified customer reviews, audit feedback, and toggle visibility.
                  </p>
                </div>
                <span className="admin-menu-link-text">
                  Moderate Reviews
                </span>
              </Link>
            </div>
          </div>
        </>
      )}
      </div>
    </>
  );
};

export default AdminDashboardPage;
