import React, { useState, useEffect } from 'react';

export const AddressForm = ({
  initialData = null,
  onSubmit,
  onCancel,
  loading = false,
  title = 'Shipping Address',
}) => {
  const [formData, setFormData] = useState({
    label: '',
    recipient_name: '',
    phone: '',
    address_line1: '',
    address_line2: '',
    barangay: '',
    city: '',
    province: '',
    postal_code: '',
    country: 'Philippines',
    is_default: false,
  });

  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (initialData) {
      setFormData({
        label: initialData.label || '',
        recipient_name: initialData.recipient_name || '',
        phone: initialData.phone || '',
        address_line1: initialData.address_line1 || '',
        address_line2: initialData.address_line2 || '',
        barangay: initialData.barangay || '',
        city: initialData.city || '',
        province: initialData.province || '',
        postal_code: initialData.postal_code || '',
        country: initialData.country || 'Philippines',
        is_default: Boolean(initialData.is_default),
      });
    }
  }, [initialData]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.recipient_name.trim()) {
      newErrors.recipient_name = 'Recipient name is required.';
    } else if (formData.recipient_name.trim().length < 2) {
      newErrors.recipient_name = 'Recipient name must be at least 2 characters.';
    }

    if (!formData.phone.trim()) {
      newErrors.phone = 'Phone number is required.';
    } else if (formData.phone.trim().length < 7) {
      newErrors.phone = 'Please enter a valid phone number.';
    }

    if (!formData.address_line1.trim()) {
      newErrors.address_line1 = 'Street address line 1 is required.';
    } else if (formData.address_line1.trim().length < 3) {
      newErrors.address_line1 = 'Address line 1 must be at least 3 characters.';
    }

    if (!formData.barangay.trim()) {
      newErrors.barangay = 'Barangay is required.';
    }

    if (!formData.city.trim()) {
      newErrors.city = 'City is required.';
    }

    if (!formData.province.trim()) {
      newErrors.province = 'Province is required.';
    }

    if (!formData.postal_code.trim()) {
      newErrors.postal_code = 'Postal code is required.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;

    onSubmit({
      ...formData,
      label: formData.label.trim() || null,
      recipient_name: formData.recipient_name.trim(),
      phone: formData.phone.trim(),
      address_line1: formData.address_line1.trim(),
      address_line2: formData.address_line2.trim() || null,
      barangay: formData.barangay.trim(),
      city: formData.city.trim(),
      province: formData.province.trim(),
      postal_code: formData.postal_code.trim(),
      country: formData.country.trim() || 'Philippines',
    });
  };

  return (
    <div className="card address-form-card">
      <div className="address-form-header">
        <h3 className="card-title">{title}</h3>
        {onCancel && (
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={onCancel}
            disabled={loading}
          >
            ✕
          </button>
        )}
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="addr-recipient" className="form-label">
              Recipient Name <span className="text-danger">*</span>
            </label>
            <input
              id="addr-recipient"
              name="recipient_name"
              type="text"
              className={`form-input ${errors.recipient_name ? 'input-error' : ''}`}
              placeholder="e.g. Juan Dela Cruz"
              value={formData.recipient_name}
              onChange={handleChange}
              disabled={loading}
            />
            {errors.recipient_name && (
              <span className="field-error">{errors.recipient_name}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="addr-phone" className="form-label">
              Phone Number <span className="text-danger">*</span>
            </label>
            <input
              id="addr-phone"
              name="phone"
              type="tel"
              className={`form-input ${errors.phone ? 'input-error' : ''}`}
              placeholder="e.g. 0917 123 4567"
              value={formData.phone}
              onChange={handleChange}
              disabled={loading}
            />
            {errors.phone && <span className="field-error">{errors.phone}</span>}
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="addr-line1" className="form-label">
              Address Line 1 <span className="text-danger">*</span>
            </label>
            <input
              id="addr-line1"
              name="address_line1"
              type="text"
              className={`form-input ${errors.address_line1 ? 'input-error' : ''}`}
              placeholder="House/Unit #, Street name"
              value={formData.address_line1}
              onChange={handleChange}
              disabled={loading}
            />
            {errors.address_line1 && (
              <span className="field-error">{errors.address_line1}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="addr-line2" className="form-label">
              Address Line 2 <span className="text-muted">(Optional)</span>
            </label>
            <input
              id="addr-line2"
              name="address_line2"
              type="text"
              className="form-input"
              placeholder="Building, Landmark, Suite"
              value={formData.address_line2}
              onChange={handleChange}
              disabled={loading}
            />
          </div>
        </div>

        <div className="form-row form-row-3">
          <div className="form-group">
            <label htmlFor="addr-barangay" className="form-label">
              Barangay <span className="text-danger">*</span>
            </label>
            <input
              id="addr-barangay"
              name="barangay"
              type="text"
              className={`form-input ${errors.barangay ? 'input-error' : ''}`}
              placeholder="e.g. San Antonio"
              value={formData.barangay}
              onChange={handleChange}
              disabled={loading}
            />
            {errors.barangay && <span className="field-error">{errors.barangay}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="addr-city" className="form-label">
              City / Municipality <span className="text-danger">*</span>
            </label>
            <input
              id="addr-city"
              name="city"
              type="text"
              className={`form-input ${errors.city ? 'input-error' : ''}`}
              placeholder="e.g. Pasig City"
              value={formData.city}
              onChange={handleChange}
              disabled={loading}
            />
            {errors.city && <span className="field-error">{errors.city}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="addr-province" className="form-label">
              Province <span className="text-danger">*</span>
            </label>
            <input
              id="addr-province"
              name="province"
              type="text"
              className={`form-input ${errors.province ? 'input-error' : ''}`}
              placeholder="e.g. Metro Manila"
              value={formData.province}
              onChange={handleChange}
              disabled={loading}
            />
            {errors.province && <span className="field-error">{errors.province}</span>}
          </div>
        </div>

        <div className="form-row form-row-3">
          <div className="form-group">
            <label htmlFor="addr-postal" className="form-label">
              Postal Code <span className="text-danger">*</span>
            </label>
            <input
              id="addr-postal"
              name="postal_code"
              type="text"
              className={`form-input ${errors.postal_code ? 'input-error' : ''}`}
              placeholder="e.g. 1600"
              value={formData.postal_code}
              onChange={handleChange}
              disabled={loading}
            />
            {errors.postal_code && (
              <span className="field-error">{errors.postal_code}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="addr-country" className="form-label">
              Country
            </label>
            <input
              id="addr-country"
              name="country"
              type="text"
              className="form-input"
              value={formData.country}
              disabled
              style={{ backgroundColor: 'var(--color-surface-muted)', cursor: 'not-allowed' }}
            />
          </div>

          <div className="form-group">
            <label htmlFor="addr-label" className="form-label">
              Label <span className="text-muted">(Optional)</span>
            </label>
            <input
              id="addr-label"
              name="label"
              type="text"
              className="form-input"
              placeholder="e.g. Home, Office"
              value={formData.label}
              onChange={handleChange}
              disabled={loading}
            />
          </div>
        </div>

        <div className="form-group form-checkbox-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="is_default"
              checked={formData.is_default}
              onChange={handleChange}
              disabled={loading}
            />
            <span>Set as default shipping address</span>
          </label>
        </div>

        <div className="address-form-actions">
          {onCancel && (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={onCancel}
              disabled={loading}
            >
              Cancel
            </button>
          )}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving Address...' : initialData ? 'Update Address' : 'Save Address'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default AddressForm;
