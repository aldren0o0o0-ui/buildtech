import React, { useState } from 'react';

export const InventoryAdjustmentForm = ({ item, onSubmit, onCancel, submitting }) => {
  const [type, setType] = useState('ADJUSTMENT_OUT');
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

    if (type === 'ADJUSTMENT_OUT') {
      if (item && item.quantity - parsedQty < 0) {
        setError(`Cannot decrease stock by ${parsedQty}. Current total quantity is ${item.quantity}.`);
        return;
      }
      if (item && (item.quantity - parsedQty) < item.reserved_quantity) {
        setError(`Cannot decrease stock below reserved quantity (${item.reserved_quantity}). Available for deduction: ${item.available_quantity}.`);
        return;
      }
    }

    onSubmit({
      type,
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
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <span className="badge badge-subtle">Total Stock: {item?.quantity}</span>
            <span className="badge badge-subtle">Reserved: {item?.reserved_quantity}</span>
            <span className="badge badge-subtle">Available: {item?.available_quantity}</span>
          </div>
        </div>

        <div className="form-group" style={{ marginTop: 'var(--space-4)' }}>
          <label htmlFor="adj-type" className="form-label">
            Adjustment Direction *
          </label>
          <select
            id="adj-type"
            className="form-input"
            value={type}
            onChange={(e) => setType(e.target.value)}
            disabled={submitting}
          >
            <option value="ADJUSTMENT_OUT">Decrease Stock (Write-off / Damage / Lost)</option>
            <option value="ADJUSTMENT_IN">Increase Stock (Found stock / Recount surplus)</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="adj-qty" className="form-label">
            Adjustment Quantity *
          </label>
          <input
            id="adj-qty"
            type="number"
            min="1"
            className="form-input"
            placeholder="e.g. 3"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            required
            disabled={submitting}
            autoFocus
          />
        </div>

        <div className="form-group">
          <label htmlFor="adj-reason" className="form-label">
            Reason / Audit Notes *
          </label>
          <input
            id="adj-reason"
            type="text"
            className="form-input"
            placeholder="e.g. Damaged packaging during warehouse handling"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            disabled={submitting}
            required
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
          {submitting ? 'Adjusting...' : 'Apply Adjustment'}
        </button>
      </div>
    </form>
  );
};

export default InventoryAdjustmentForm;
