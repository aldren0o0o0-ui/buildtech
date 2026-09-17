import React from 'react';

export const AvailabilityBadge = ({ status }) => {
  const norm = (status || '').toUpperCase();

  if (norm === 'IN_STOCK') {
    return (
      <span className="badge badge-in-stock" title="Item is in stock and ready to ship">
        ● In Stock
      </span>
    );
  }

  if (norm === 'LOW_STOCK') {
    return (
      <span className="badge badge-low-stock" title="Limited quantity remaining">
        ▲ Low Stock
      </span>
    );
  }

  return (
    <span className="badge badge-out-of-stock" title="Item is currently out of stock">
      ✕ Out of Stock
    </span>
  );
};

export default AvailabilityBadge;
