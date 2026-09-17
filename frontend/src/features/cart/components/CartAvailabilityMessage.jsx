import React from 'react';

export const CartAvailabilityMessage = ({ items }) => {
  if (!items || items.length === 0) return null;

  const unavailableItems = items.filter((item) => !item.is_available);
  if (unavailableItems.length === 0) return null;

  return (
    <div className="alert alert-warning cart-availability-banner" role="alert">
      <div className="cart-availability-header">
        <svg
          className="cart-availability-icon"
          viewBox="0 0 24 24"
          width="16"
          height="16"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <strong>Some items in your cart require attention:</strong>
      </div>
      <ul className="cart-availability-list">
        {unavailableItems.map((item) => (
          <li key={item.id}>
            <strong>{item.product.name}</strong>:{' '}
            {item.availability_reason || 'Item is currently unavailable.'}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default CartAvailabilityMessage;
