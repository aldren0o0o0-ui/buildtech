import React, { useEffect, useState, useCallback } from 'react';
import brandService from '../services/brandService';
import { AdminNav } from '../../../admin';

export const AdminBrandsPage = () => {
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Modal State for Add / Edit
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingBrand, setEditingBrand] = useState(null);
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    logoUrl: '',
    isActive: true,
  });

  const loadBrands = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await brandService.listBrands({ include_inactive: true });
      setBrands(data);
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Unable to load brands. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBrands();
  }, [loadBrands]);

  // Open Create Modal
  const handleOpenCreate = () => {
    setEditingBrand(null);
    setFormData({
      name: '',
      description: '',
      logoUrl: '',
      isActive: true,
    });
    setFormError('');
    setIsModalOpen(true);
  };

  // Open Edit Modal
  const handleOpenEdit = (brand) => {
    setEditingBrand(brand);
    setFormData({
      name: brand.name,
      description: brand.description || '',
      logoUrl: brand.logo_url || '',
      isActive: brand.is_active,
    });
    setFormError('');
    setIsModalOpen(true);
  };

  // Close Modal
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingBrand(null);
    setFormError('');
  };

  // Handle Form Change
  const handleFormChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    if (formError) setFormError('');
  };

  // Handle Submit (Create or Update)
  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    const trimmedName = formData.name.trim();
    if (!trimmedName) {
      setFormError('Brand name is required.');
      return;
    }

    setFormSubmitting(true);
    try {
      if (editingBrand) {
        // Update Brand
        await brandService.updateBrand(editingBrand.id, {
          name: trimmedName,
          description: formData.description.trim() || null,
          logo_url: formData.logoUrl.trim() || null,
          is_active: formData.isActive,
        });
        setSuccess(`Brand '${trimmedName}' updated successfully.`);
      } else {
        // Create Brand
        await brandService.createBrand({
          name: trimmedName,
          description: formData.description.trim() || null,
          logo_url: formData.logoUrl.trim() || null,
          is_active: formData.isActive,
        });
        setSuccess(`Brand '${trimmedName}' created successfully.`);
      }

      handleCloseModal();
      await loadBrands();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setFormError(
        typeof detail === 'string'
          ? detail
          : 'Failed to save brand. Please check your inputs.'
      );
    } finally {
      setFormSubmitting(false);
    }
  };

  // Toggle Active Status
  const handleToggleActive = async (brand) => {
    setError('');
    setSuccess('');
    try {
      const newStatus = !brand.is_active;
      await brandService.updateBrand(brand.id, {
        is_active: newStatus,
      });
      setSuccess(
        `Brand '${brand.name}' ${newStatus ? 'activated' : 'deactivated'} successfully.`
      );
      await loadBrands();
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to update brand status.'
      );
    }
  };

  // Delete Brand
  const handleDelete = async (brand) => {
    if (
      !window.confirm(
        `Are you sure you want to permanently delete brand '${brand.name}'?`
      )
    ) {
      return;
    }

    setError('');
    setSuccess('');
    try {
      await brandService.deleteBrand(brand.id);
      setSuccess(`Brand '${brand.name}' deleted successfully.`);
      await loadBrands();
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to delete brand.'
      );
    }
  };

  return (
    <>
      <AdminNav activeTitle="Brands Management" />
      <div className="container page-wrapper" style={{ paddingTop: 0 }}>
        {/* Header */}
        <div className="page-action-header">
          <div className="page-action-header-left">
            <h1 className="admin-title">Brands Management</h1>
            <p className="admin-subtitle">
              Manage hardware manufacturers and brand entities.
            </p>
          </div>

          <button
          type="button"
          onClick={handleOpenCreate}
          className="btn btn-primary"
        >
          + Add Brand
        </button>
      </div>

      {/* Alerts */}
      {success && (
        <div className="alert alert-success" role="alert" aria-live="polite">
          <span>{success}</span>
        </div>
      )}

      {error && (
        <div className="alert alert-danger" role="alert" aria-live="polite">
          <span>{error}</span>
        </div>
      )}

      {/* Content Table */}
      {loading ? (
        <div className="spinner-wrapper" role="status">
          <div className="spinner" aria-hidden="true"></div>
          <p>Loading brands...</p>
        </div>
      ) : brands.length === 0 ? (
        <div className="card empty-table-box">
          <h3 className="empty-table-title">No brands yet</h3>
          <p>Click "Add Brand" above to register your first hardware brand.</p>
        </div>
      ) : (
        <div className="data-table-wrapper table-responsive-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Brand Name</th>
                <th>Slug</th>
                <th>Description</th>
                <th>Logo URL</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {brands.map((brand) => (
                <tr key={brand.id}>
                  <td className="table-col-name">{brand.name}</td>
                  <td className="table-col-slug">{brand.slug}</td>
                  <td style={{ color: 'var(--color-text-secondary)' }}>
                    {brand.description || '—'}
                  </td>
                  <td style={{ color: 'var(--color-text-secondary)', fontSize: '0.8125rem' }}>
                    {brand.logo_url ? (
                      <span title={brand.logo_url} style={{ maxWidth: '180px', display: 'inline-block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {brand.logo_url}
                      </span>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        brand.is_active ? 'badge-active' : 'badge-inactive'
                      }`}
                    >
                      {brand.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="table-actions-cell">
                    <div className="table-action-group">
                      <button
                        type="button"
                        onClick={() => handleOpenEdit(brand)}
                        className="btn btn-outline btn-sm"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => handleToggleActive(brand)}
                        className="btn btn-ghost btn-sm"
                      >
                        {brand.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(brand)}
                        className="btn btn-ghost btn-sm"
                        style={{ color: 'var(--color-danger)' }}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Add / Edit Modal */}
      {isModalOpen && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal-card">
            <div className="modal-header">
              <h2 className="modal-title">
                {editingBrand ? 'Edit Brand' : 'Add New Brand'}
              </h2>
              <button
                type="button"
                onClick={handleCloseModal}
                className="modal-close-btn"
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleFormSubmit} noValidate>
              <div className="modal-body">
                {formError && (
                  <div className="alert alert-danger" role="alert">
                    <span>{formError}</span>
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="brand-name" className="form-label">
                    Brand Name *
                  </label>
                  <input
                    id="brand-name"
                    type="text"
                    name="name"
                    className="form-input"
                    placeholder="e.g. Corsair"
                    value={formData.name}
                    onChange={handleFormChange}
                    autoFocus
                    required
                    disabled={formSubmitting}
                  />
                  <span className="form-helper">
                    Slug is automatically generated from the brand name.
                  </span>
                </div>

                <div className="form-group">
                  <label htmlFor="brand-desc" className="form-label">
                    Description
                  </label>
                  <textarea
                    id="brand-desc"
                    name="description"
                    className="form-input"
                    style={{ height: '75px', padding: '0.5rem 0.75rem', resize: 'vertical' }}
                    placeholder="Optional manufacturer description"
                    value={formData.description}
                    onChange={handleFormChange}
                    disabled={formSubmitting}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="brand-logo" className="form-label">
                    Logo URL
                  </label>
                  <input
                    id="brand-logo"
                    type="url"
                    name="logoUrl"
                    className="form-input"
                    placeholder="https://example.com/logo.svg (optional)"
                    value={formData.logoUrl}
                    onChange={handleFormChange}
                    disabled={formSubmitting}
                  />
                </div>

                <div className="form-group">
                  <label className="form-checkbox-label">
                    <input
                      type="checkbox"
                      name="isActive"
                      className="form-checkbox"
                      checked={formData.isActive}
                      onChange={handleFormChange}
                      disabled={formSubmitting}
                    />
                    Active (visible in public catalog)
                  </label>
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="btn btn-outline"
                  disabled={formSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={formSubmitting}
                >
                  {formSubmitting
                    ? 'Saving...'
                    : editingBrand
                    ? 'Save Changes'
                    : 'Create Brand'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      </div>
    </>
  );
};

export default AdminBrandsPage;
