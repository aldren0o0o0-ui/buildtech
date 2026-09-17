import React from 'react';

export const InventoryHistory = ({ transactions, loading, onClose }) => {
  const formatDate = (isoString) => {
    if (!isoString) return '—';
    return new Date(isoString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  return (
    <div>
      <div className="modal-body" style={{ maxHeight: '60vh', overflowY: 'auto' }}>
        {loading ? (
          <div className="spinner-wrapper" style={{ minHeight: '160px' }}>
            <div className="spinner"></div>
            <p>Loading transaction audit trail...</p>
          </div>
        ) : transactions.length === 0 ? (
          <div className="empty-table-box" style={{ padding: 'var(--space-6)' }}>
            <p style={{ margin: 0 }}>No inventory transactions recorded yet for this product.</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Date & Time</th>
                <th>Type</th>
                <th style={{ textAlign: 'right' }}>Change</th>
                <th style={{ textAlign: 'right' }}>Before</th>
                <th style={{ textAlign: 'right' }}>After</th>
                <th>Reason / Reference</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.id}>
                  <td style={{ whiteSpace: 'nowrap', fontSize: '0.8125rem' }}>
                    {formatDate(tx.created_at)}
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        tx.type === 'STOCK_IN'
                          ? 'badge-in-stock'
                          : tx.type === 'ADJUSTMENT_IN'
                          ? 'badge-customer'
                          : 'badge-low-stock'
                      }`}
                    >
                      {tx.type}
                    </span>
                  </td>
                  <td
                    style={{
                      textAlign: 'right',
                      fontWeight: 700,
                      color: tx.quantity_change > 0 ? 'var(--color-success)' : 'var(--color-danger)',
                    }}
                  >
                    {tx.quantity_change > 0 ? `+${tx.quantity_change}` : tx.quantity_change}
                  </td>
                  <td style={{ textAlign: 'right', color: 'var(--color-text-secondary)' }}>
                    {tx.quantity_before}
                  </td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>
                    {tx.quantity_after}
                  </td>
                  <td style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
                    {tx.reason || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="modal-footer">
        <button type="button" onClick={onClose} className="btn btn-outline">
          Close
        </button>
      </div>
    </div>
  );
};

export default InventoryHistory;
