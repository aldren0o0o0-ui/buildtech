import React from 'react';

export const OrderStatusBadge = ({ status }) => {
  const getBadgeConfig = (st) => {
    switch (st) {
      case 'PENDING':
        return { className: 'badge-warning', label: 'Pending' };
      case 'CONFIRMED':
        return { className: 'badge-success', label: 'Confirmed' };
      case 'PROCESSING':
        return { className: 'badge-primary', label: 'Processing' };
      case 'SHIPPED':
        return { className: 'badge-info', label: 'Shipped' };
      case 'DELIVERED':
        return { className: 'badge-success', label: 'Delivered' };
      case 'READY_FOR_FULFILLMENT':
        return { className: 'badge-info', label: 'Ready for Fulfillment' };
      case 'COMPLETED':
        return { className: 'badge-success', label: 'Completed' };
      case 'CANCELLED':
        return { className: 'badge-danger', label: 'Cancelled' };
      default:
        return { className: 'badge-muted', label: st || 'Unknown' };
    }
  };

  const config = getBadgeConfig(status);

  return (
    <span className={`badge ${config.className}`}>
      {config.label}
    </span>
  );
};

export default OrderStatusBadge;
