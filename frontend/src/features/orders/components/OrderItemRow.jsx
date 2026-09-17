import React from 'react';

export const OrderItemRow = ({ item }) => {
  const formattedUnitPrice = Number(item.unit_price).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });

  const formattedSubtotal = Number(item.subtotal).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });

  return (
    <div className="order-item-row" style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: 'var(--space-4) 0',
      borderBottom: '1px solid var(--color-border)',
      gap: 'var(--space-4)',
    }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <h4 style={{
          fontSize: '0.9375rem',
          fontWeight: '600',
          color: 'var(--color-text)',
          marginBottom: 'var(--space-1)',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}>
          {item.product_name}
        </h4>
        <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-secondary)' }}>
          SKU: <code>{item.sku || item.product_sku}</code>
        </div>
      </div>

      <div style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
        <div style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-1)' }}>
          {item.quantity} × {formattedUnitPrice}
        </div>
        <div style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--color-text)' }}>
          {formattedSubtotal}
        </div>
      </div>
    </div>
  );
};

export default OrderItemRow;
