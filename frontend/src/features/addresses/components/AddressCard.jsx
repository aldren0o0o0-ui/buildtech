import React from 'react';

export const AddressCard = ({
  address,
  onEdit,
  onDelete,
  onSetDefault,
  selectable = false,
  selected = false,
  onSelect,
  disabled = false,
}) => {
  if (!address) return null;

  const formattedAddress = [
    address.address_line1,
    address.address_line2,
    `Brgy. ${address.barangay}`,
    address.city,
    address.province,
    address.postal_code,
    address.country,
  ]
    .filter(Boolean)
    .join(', ');

  const handleCardClick = () => {
    if (selectable && onSelect && !disabled) {
      onSelect(address);
    }
  };

  return (
    <div
      className={`card address-card ${selectable ? 'address-card-selectable' : ''} ${
        selected ? 'address-card-selected' : ''
      }`}
      onClick={handleCardClick}
      role={selectable ? 'button' : undefined}
      tabIndex={selectable ? 0 : undefined}
      onKeyDown={(e) => {
        if (selectable && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          handleCardClick();
        }
      }}
    >
      <div className="address-card-header">
        <div className="address-meta-row">
          {selectable && (
            <div className="address-select-radio" aria-hidden="true">
              <span className={`radio-dot ${selected ? 'radio-dot-active' : ''}`} />
            </div>
          )}
          <span className="address-recipient">{address.recipient_name}</span>
          {address.label && (
            <span className="badge badge-subtle address-label-pill">{address.label}</span>
          )}
          {address.is_default && (
            <span className="badge badge-primary address-default-pill">Default</span>
          )}
        </div>
      </div>

      <div className="address-card-body">
        <p className="address-line-text">{formattedAddress}</p>
        <p className="address-phone-text">{address.phone}</p>
      </div>

      {/* Card Actions for Management Mode */}
      {!selectable && (
        <div className="address-card-footer">
          <div className="address-actions-left">
            {!address.is_default && onSetDefault && (
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onSetDefault(address.id);
                }}
                disabled={disabled}
              >
                Set as Default
              </button>
            )}
          </div>
          <div className="address-actions-right">
            {onEdit && (
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(address);
                }}
                disabled={disabled}
              >
                Edit
              </button>
            )}
            {onDelete && (
              <button
                type="button"
                className="btn btn-ghost btn-sm btn-danger-text"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(address.id);
                }}
                disabled={disabled}
              >
                Delete
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AddressCard;
