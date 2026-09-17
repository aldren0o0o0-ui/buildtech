import React from 'react';
import { Link } from 'react-router-dom';

export const EmptyCart = () => {
  return (
    <div className="empty-state-box">
      <h2 className="empty-title">Your cart is empty</h2>
      <p className="empty-desc">
        Browse products to get started.
      </p>
      <Link to="/products" className="btn btn-primary btn-sm">
        Browse Products
      </Link>
    </div>
  );
};

export default EmptyCart;
