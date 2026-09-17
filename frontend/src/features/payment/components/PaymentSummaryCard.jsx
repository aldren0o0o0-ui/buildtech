import { useState } from 'react';
import paymentService from '../services/paymentService';

export const PaymentSummaryCard = ({
  payment,
  isAdmin = false,
  onPaymentUpdated = null,
}) => {
  const [markingPaid, setMarkingPaid] = useState(false);
  const [actionError, setActionError] = useState('');
  const [actionSuccess, setActionSuccess] = useState('');

  if (!payment) {
    return (
      <div className="card payment-summary-card">
        <h2 className="card-title" style={{ marginBottom: 'var(--space-2)' }}>
          Payment Information
        </h2>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
          No payment record associated with this order.
        </p>
      </div>
    );
  }

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'PAID':
        return 'badge-success';
      case 'PENDING':
        return 'badge-warning';
      case 'CANCELLED':
        return 'badge-danger';
      case 'REFUNDED':
        return 'badge-info';
      case 'FAILED':
        return 'badge-danger';
      default:
        return 'badge-muted';
    }
  };

  const formattedAmount = Number(payment.amount).toLocaleString('en-PH', {
    style: 'currency',
    currency: payment.currency || 'PHP',
  });

  const formattedCreated = payment.created_at
    ? new Date(payment.created_at).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : null;

  const formattedPaidAt = payment.paid_at
    ? new Date(payment.paid_at).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : null;

  const formattedCancelledAt = payment.cancelled_at
    ? new Date(payment.cancelled_at).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : null;

  const handleMarkCodPaid = async () => {
    if (!isAdmin || payment.status !== 'PENDING') return;

    setMarkingPaid(true);
    setActionError('');
    setActionSuccess('');

    try {
      const updated = await paymentService.markCodPaymentPaid(payment.id);
      setActionSuccess('Payment has been successfully marked as PAID.');
      if (onPaymentUpdated) {
        onPaymentUpdated(updated);
      }
    } catch (err) {
      setActionError(
        err.response?.data?.detail || 'Failed to mark payment as paid.'
      );
    } finally {
      setMarkingPaid(false);
    }
  };

  const isCod =
    payment.method === 'CASH_ON_DELIVERY' || payment.method === 'COD';
  const canAdminMarkPaid = isAdmin && isCod && payment.status === 'PENDING';

  return (
    <div className="card payment-summary-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
        <h2 className="card-title" style={{ margin: 0 }}>
          Payment Details
        </h2>
        <span className={`badge ${getStatusBadgeClass(payment.status)}`}>
          {payment.status}
        </span>
      </div>

      {actionSuccess && (
        <div className="alert alert-success" style={{ marginBottom: 'var(--space-3)', padding: '0.5rem 0.75rem', fontSize: '0.8125rem' }}>
          <span>{actionSuccess}</span>
        </div>
      )}

      {actionError && (
        <div className="alert alert-danger" style={{ marginBottom: 'var(--space-3)', padding: '0.5rem 0.75rem', fontSize: '0.8125rem' }}>
          <span>{actionError}</span>
        </div>
      )}

      <div style={{ fontSize: '0.875rem', lineHeight: 1.7, color: 'var(--color-text-secondary)' }}>
        <p>
          Reference: <strong style={{ color: 'var(--color-text)', letterSpacing: '0.5px' }}>{payment.payment_reference}</strong>
        </p>
        <p>
          Method: <strong style={{ color: 'var(--color-text)' }}>{isCod ? 'Cash on Delivery' : payment.method}</strong>
        </p>
        <p>
          Amount Payable:{' '}
          <strong style={{ color: 'var(--color-primary)', fontSize: '1rem', fontWeight: 600 }}>
            {formattedAmount}
          </strong>
        </p>
        {formattedPaidAt && (
          <p>
            Paid At: <strong style={{ color: 'var(--color-success)' }}>{formattedPaidAt}</strong>
          </p>
        )}
        {formattedCancelledAt && (
          <p>
            Cancelled At: <strong style={{ color: 'var(--color-danger)' }}>{formattedCancelledAt}</strong>
          </p>
        )}
        {formattedCreated && (
          <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 'var(--space-2)' }}>
            Initiated on: {formattedCreated}
          </p>
        )}
      </div>

      {canAdminMarkPaid && (
        <div style={{ marginTop: 'var(--space-4)', borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-3)' }}>
          <button
            type="button"
            className="btn btn-success btn-sm"
            style={{ width: '100%' }}
            disabled={markingPaid}
            onClick={handleMarkCodPaid}
          >
            {markingPaid ? 'Recording Payment...' : 'Mark COD as Paid'}
          </button>
          <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: '0.25rem', textAlign: 'center' }}>
            Authorizes cash receipt from delivery courier
          </span>
        </div>
      )}
    </div>
  );
};

export default PaymentSummaryCard;
