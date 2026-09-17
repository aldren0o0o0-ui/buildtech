import React from 'react';

export const OrderSummary = ({ order }) => {
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

  return (
    <div className="card order-summary-card" style={{ padding: 'var(--space-6)' }}>
      <h3 style={{ fontSize: '1.125rem', fontWeight: '700', marginBottom: 'var(--space-4)' }}>
        Order Financial Summary
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9375rem' }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>Items Subtotal</span>
          <span style={{ fontWeight: '500' }}>{formattedSubtotal}</span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9375rem' }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>Shipping Fee</span>
          <span style={{ fontWeight: '500' }}>
            {Number(order.shipping_fee) === 0 ? 'FREE' : formattedShipping}
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9375rem' }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>Estimated Tax</span>
          <span style={{ fontWeight: '500' }}>$0.00</span>
        </div>

        <div style={{
          height: '1px',
          backgroundColor: 'var(--color-border)',
          margin: 'var(--space-2) 0',
        }} />

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '1.125rem',
          fontWeight: '700',
          color: 'var(--color-text)',
        }}>
          <span>Total</span>
          <span style={{ color: 'var(--color-primary)' }}>{formattedTotal}</span>
        </div>
      </div>
    </div>
  );
};

export default OrderSummary;
