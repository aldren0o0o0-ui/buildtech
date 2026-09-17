import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import reviewService from '../services/reviewService';
import RatingStars from '../components/RatingStars';
import { AdminNav } from '../../admin';

export const AdminReviewsPage = () => {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalReviews, setTotalReviews] = useState(0);

  const [actionLoadingId, setActionLoadingId] = useState(null);

  const fetchReviews = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await reviewService.adminListReviews(
        page,
        15,
        statusFilter || null,
        search.trim() || null
      );
      setReviews(data.items || []);
      setTotalPages(data.pages || 1);
      setTotalReviews(data.total || 0);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load reviews.');
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter, search]);

  useEffect(() => {
    fetchReviews();
  }, [fetchReviews]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchReviews();
  };

  const handleStatusChange = async (reviewId, newStatus) => {
    setActionLoadingId(reviewId);
    setSuccessMsg('');
    setError('');
    try {
      await reviewService.adminUpdateStatus(reviewId, newStatus);
      setSuccessMsg(`Review #${reviewId} status updated to ${newStatus}.`);
      await fetchReviews();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update review status.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDelete = async (reviewId) => {
    if (!window.confirm(`Are you sure you want to permanently delete Review #${reviewId}?`)) {
      return;
    }
    setActionLoadingId(reviewId);
    setSuccessMsg('');
    setError('');
    try {
      await reviewService.adminDeleteReview(reviewId);
      setSuccessMsg(`Review #${reviewId} has been permanently deleted.`);
      await fetchReviews();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete review.');
    } finally {
      setActionLoadingId(null);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    try {
      const d = new Date(dateString);
      return d.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  return (
    <>
      <AdminNav activeTitle="Review Moderation" />
      <div className="container page-wrapper" style={{ paddingTop: 0 }}>
        <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
          <div>
            <h1 className="page-title" style={{ margin: 0 }}>Review Moderation</h1>
            <p className="page-subtitle" style={{ margin: 'var(--space-1) 0 0 0', color: 'var(--color-text-secondary)' }}>
              Moderate verified customer reviews, toggle visibility, or delete inappropriate feedback.
            </p>
          </div>
          <div>
            <span className="badge badge-primary" style={{ padding: '6px 12px', fontSize: '0.875rem' }}>
              Total: {totalReviews}
            </span>
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="alert alert-danger" style={{ marginBottom: 'var(--space-4)' }}>
            <span>{error}</span>
          </div>
        )}
        {successMsg && (
          <div className="alert alert-success" style={{ marginBottom: 'var(--space-4)' }}>
            <span>{successMsg}</span>
          </div>
        )}

      {/* Filter and Search Bar */}
      <div className="card admin-filter-card" style={{ padding: 'var(--space-4)', marginBottom: 'var(--space-6)' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div style={{ flex: 1, minWidth: '220px' }}>
            <label htmlFor="admin-review-search" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 'var(--space-1)' }}>
              Search Reviews
            </label>
            <input
              id="admin-review-search"
              type="text"
              className="input"
              placeholder="Search by author, title, comment..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ minWidth: '160px' }}>
            <label htmlFor="admin-review-status" style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: 'var(--space-1)' }}>
              Status Filter
            </label>
            <select
              id="admin-review-status"
              className="input"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              style={{ width: '100%' }}
            >
              <option value="">All Statuses</option>
              <option value="PUBLISHED">Published</option>
              <option value="HIDDEN">Hidden</option>
            </select>
          </div>

          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <button type="submit" className="btn btn-primary">
              Filter
            </button>
            <button
              type="button"
              className="btn btn-outline"
              onClick={() => {
                setSearch('');
                setStatusFilter('');
                setPage(1);
              }}
            >
              Reset
            </button>
          </div>
        </form>
      </div>

      {/* Reviews Table */}
      <div className="card table-wrapper table-responsive-wrapper" style={{ padding: 0 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 'var(--space-8)' }}>
            <div className="spinner" style={{ margin: '0 auto var(--space-2)' }} />
            <p style={{ color: 'var(--color-text-secondary)' }}>Loading reviews...</p>
          </div>
        ) : reviews.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 'var(--space-8)' }}>
            <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>No reviews match the specified criteria.</p>
          </div>
        ) : (
          <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border-subtle, rgba(255,255,255,0.1))' }}>
                <th style={{ padding: 'var(--space-3)' }}>ID</th>
                <th style={{ padding: 'var(--space-3)' }}>Product</th>
                <th style={{ padding: 'var(--space-3)' }}>Author</th>
                <th style={{ padding: 'var(--space-3)' }}>Rating</th>
                <th style={{ padding: 'var(--space-3)' }}>Review Content</th>
                <th style={{ padding: 'var(--space-3)' }}>Status</th>
                <th style={{ padding: 'var(--space-3)' }}>Date</th>
                <th style={{ padding: 'var(--space-3)', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {reviews.map((r) => {
                const isLoading = actionLoadingId === r.id;
                return (
                  <tr
                    key={r.id}
                    style={{
                      borderBottom: '1px solid var(--color-border-subtle, rgba(255,255,255,0.05))',
                      opacity: isLoading ? 0.6 : 1
                    }}
                  >
                    <td style={{ padding: 'var(--space-3)', fontWeight: 600 }}>#{r.id}</td>
                    <td style={{ padding: 'var(--space-3)' }}>
                      {r.product ? (
                        <Link
                          to={`/products/${r.product.slug || r.product.id}`}
                          style={{ color: 'var(--color-primary, #6366f1)', textDecoration: 'none', fontWeight: 500 }}
                          target="_blank"
                          rel="noreferrer"
                        >
                          {r.product.name}
                        </Link>
                      ) : (
                        <span style={{ color: 'var(--color-text-secondary)' }}>Product #{r.product_id}</span>
                      )}
                    </td>
                    <td style={{ padding: 'var(--space-3)' }}>
                      <div style={{ fontWeight: 500 }}>{r.author_name || 'Customer'}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                        User #{r.user_id}
                      </div>
                    </td>
                    <td style={{ padding: 'var(--space-3)' }}>
                      <RatingStars rating={r.rating} size="sm" showValue />
                    </td>
                    <td style={{ padding: 'var(--space-3)', maxWidth: '280px' }}>
                      {r.title && (
                        <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '2px' }}>
                          {r.title}
                        </div>
                      )}
                      <div
                        style={{
                          fontSize: '0.825rem',
                          color: 'var(--color-text-secondary)',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}
                      >
                        {r.comment || <em style={{ color: 'var(--color-text-tertiary)' }}>No written comment</em>}
                      </div>
                    </td>
                    <td style={{ padding: 'var(--space-3)' }}>
                      <span
                        className={`badge ${r.status === 'PUBLISHED' ? 'badge-success' : 'badge-warning'}`}
                        style={{
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 600
                        }}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td style={{ padding: 'var(--space-3)', fontSize: '0.825rem', color: 'var(--color-text-secondary)' }}>
                      {formatDate(r.created_at)}
                    </td>
                    <td style={{ padding: 'var(--space-3)', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: 'var(--space-2)' }}>
                        {r.status === 'PUBLISHED' ? (
                          <button
                            type="button"
                            className="btn btn-outline btn-sm"
                            style={{ fontSize: '0.75rem', padding: '3px 8px' }}
                            onClick={() => handleStatusChange(r.id, 'HIDDEN')}
                            disabled={isLoading}
                          >
                            Hide
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            style={{ fontSize: '0.75rem', padding: '3px 8px' }}
                            onClick={() => handleStatusChange(r.id, 'PUBLISHED')}
                            disabled={isLoading}
                          >
                            Publish
                          </button>
                        )}
                        <button
                          type="button"
                          className="btn btn-danger-outline btn-sm"
                          style={{ fontSize: '0.75rem', padding: '3px 8px' }}
                          onClick={() => handleDelete(r.id)}
                          disabled={isLoading}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {!loading && totalPages > 1 && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 'var(--space-3)',
            marginTop: 'var(--space-6)'
          }}
        >
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
          >
            ← Previous
          </button>
          <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
            Page {page} of {totalPages}
          </span>
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            Next →
          </button>
        </div>
      )}
      </div>
    </>
  );
};

export default AdminReviewsPage;
