import React, { useState } from 'react';

export const StockInForm = ({ item, onSubmit, onCancel, submitting }) => {
  const [quantity, setQuantity] = useState('');
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    const parsedQty = parseInt(quantity, 10);
    if (isNaN(parsedQty) || parsedQty <= 0) {
      setError('Please enter a valid positive quantity greater than 0.');
      return;
    }

    onSubmit({
      quantity: parsedQty,
      reason: reason.trim() || undefined,
    });
  };

  return (
    <form onSubmit={handleSubmit} noValidate>
      <div className="modal-body">
        {error && (
          <div className="alert alert-danger" role="alert">
            <span>{error}</span>
          </div>
        )}

        <div className="stock-summary-box">
          <p style={{ margin: 0, fontSize: '0.875rem' }}>
            Product: <strong>{item?.product?.name}</strong>
          </p>
          <p style={{ margin: '0.25rem 0 0', fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
            SKU: <span style={{ fontFamily: 'var(--font-mono)' }}>{item?.product?.sku}</span>
          </p>
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '1rem' }}>
            <span className="badge badge-subtle">Current Stock: {item?.quantity}</span>
            <span className="badge badge-subtle">Available: {item?.available_quantity}</span>
          </div>
        </div>

        <div className="form-group" style={{ marginTop: 'var(--space-4)' }}>
          <label htmlFor="stockin-qty" className="form-label">
            Quantity to Add *
          </label>
          <input
            id="stockin-qty"
            type="number"
            min="1"
            className="form-input"
            placeholder="e.g. 20"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            required
            disabled={submitting}
            autoFocus
          />
        </div>

        <div className="form-group">
          <label htmlFor="stockin-reason" className="form-label">
            Restock Reason / Reference
          </label>
          <input
            id="stockin-reason"
            type="text"
            className="form-input"
            placeholder="e.g. Supplier Shipment #PO-1049"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={submitting}
          />
        </div>
      </div>

      <div className="modal-footer">
        <button
          type="button"
          onClick={onCancel}
          className="btn btn-outline"
          disabled={submitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting}
        >
          {submitting ? 'Receiving...' : 'Add Stock'}
        </button>
      </div>
    </form>
  );
};

export default StockInForm;
