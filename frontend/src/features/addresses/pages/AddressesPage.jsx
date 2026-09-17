import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import addressService from '../services/addressService';
import AddressCard from '../components/AddressCard';
import AddressForm from '../components/AddressForm';
import AddressEmpty from '../components/AddressEmpty';

export const AddressesPage = () => {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Form Modal / View State
  const [showForm, setShowForm] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);
  const [formSubmitting, setFormSubmitting] = useState(false);

  const fetchAddresses = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await addressService.getAddresses();
      setAddresses(data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Failed to load your saved addresses. Please try refreshing.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAddresses();
  }, [fetchAddresses]);

  const handleOpenCreate = () => {
    setEditingAddress(null);
    setShowForm(true);
    setSuccessMsg('');
    setError('');
  };

  const handleOpenEdit = (address) => {
    setEditingAddress(address);
    setShowForm(true);
    setSuccessMsg('');
    setError('');
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingAddress(null);
  };

  const handleFormSubmit = async (formData) => {
    setFormSubmitting(true);
    setError('');
    setSuccessMsg('');
    try {
      if (editingAddress) {
        await addressService.updateAddress(editingAddress.id, formData);
        setSuccessMsg('Address updated successfully.');
      } else {
        await addressService.createAddress(formData);
        setSuccessMsg('Address added successfully.');
      }
      setShowForm(false);
      setEditingAddress(null);
      await fetchAddresses();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'An error occurred while saving the address. Please check your inputs.'
      );
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleDelete = async (addressId) => {
    if (!window.confirm('Are you sure you want to delete this address?')) {
      return;
    }
    setError('');
    setSuccessMsg('');
    try {
      await addressService.deleteAddress(addressId);
      setSuccessMsg('Address deleted successfully.');
      await fetchAddresses();
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to delete address. Please try again.'
      );
    }
  };

  const handleSetDefault = async (addressId) => {
    setError('');
    setSuccessMsg('');
    try {
      await addressService.setDefaultAddress(addressId);
      setSuccessMsg('Default shipping address updated.');
      await fetchAddresses();
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to update default address.'
      );
    }
  };

  return (
    <div className="container page-wrapper">
      <div className="account-container">
        {/* Navigation Breadcrumb */}
        <div className="address-breadcrumb" style={{ marginBottom: 'var(--space-4)' }}>
          <Link to="/account" className="back-link">
            ← Back to Account Settings
          </Link>
        </div>

        {/* Header */}
        <div className="account-header-block" style={{ marginBottom: 'var(--space-6)' }}>
          <div>
            <h1 className="account-title">Saved Shipping Addresses</h1>
            <p className="account-email-sub">
              Manage your delivery addresses for seamless checkout.
            </p>
          </div>
          {!showForm && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleOpenCreate}
            >
              + Add New Address
            </button>
          )}
        </div>

        {/* Feedback Alerts */}
        {successMsg && (
          <div className="alert alert-success" role="alert" aria-live="polite">
            <span>{successMsg}</span>
          </div>
        )}

        {error && (
          <div className="alert alert-danger" role="alert" aria-live="polite">
            <span>{error}</span>
          </div>
        )}

        {/* Address Form (Creation or Edit Mode) */}
        {showForm && (
          <div style={{ marginBottom: 'var(--space-8)' }}>
            <AddressForm
              initialData={editingAddress}
              onSubmit={handleFormSubmit}
              onCancel={handleCloseForm}
              loading={formSubmitting}
              title={editingAddress ? 'Edit Shipping Address' : 'Add New Shipping Address'}
            />
          </div>
        )}

        {/* Address List */}
        {loading ? (
          <div className="address-grid">
            {[1, 2].map((i) => (
              <div key={i} className="card address-card skeleton-card" style={{ height: '180px' }} />
            ))}
          </div>
        ) : addresses.length === 0 && !showForm ? (
          <AddressEmpty onAddNew={handleOpenCreate} />
        ) : (
          <div className="address-grid">
            {addresses.map((addr) => (
              <AddressCard
                key={addr.id}
                address={addr}
                onEdit={handleOpenEdit}
                onDelete={handleDelete}
                onSetDefault={handleSetDefault}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AddressesPage;
