import React from 'react';

export const AddressEmpty = ({ onAddNew }) => {
  return (
    <div className="empty-state-box">
      <svg
        className="empty-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
        <circle cx="12" cy="10" r="3" />
      </svg>
      <h3 className="empty-title">No Saved Addresses</h3>
      <p className="empty-desc">
        Add a delivery address to complete your orders faster.
      </p>
      {onAddNew && (
        <button type="button" className="btn btn-primary btn-sm" onClick={onAddNew}>
          Add Address
        </button>
      )}
    </div>
  );
};

export default AddressEmpty;

