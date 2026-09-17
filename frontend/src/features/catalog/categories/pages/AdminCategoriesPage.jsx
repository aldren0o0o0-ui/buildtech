import React, { useEffect, useState, useCallback } from 'react';
import categoryService from '../services/categoryService';
import { AdminNav } from '../../../admin';

export const AdminCategoriesPage = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Modal State for Add / Edit
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    isActive: true,
  });

  const loadCategories = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await categoryService.listCategories({ include_inactive: true });
      setCategories(data);
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Unable to load categories. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  // Open Create Modal
  const handleOpenCreate = () => {
    setEditingCategory(null);
    setFormData({
      name: '',
      description: '',
      isActive: true,
    });
    setFormError('');
    setIsModalOpen(true);
  };

  // Open Edit Modal
  const handleOpenEdit = (category) => {
    setEditingCategory(category);
    setFormData({
      name: category.name,
      description: category.description || '',
      isActive: category.is_active,
    });
    setFormError('');
    setIsModalOpen(true);
  };

  // Close Modal
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingCategory(null);
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
      setFormError('Category name is required.');
      return;
    }

    setFormSubmitting(true);
    try {
      if (editingCategory) {
        // Update Category
        await categoryService.updateCategory(editingCategory.id, {
          name: trimmedName,
          description: formData.description.trim() || null,
          is_active: formData.isActive,
        });
        setSuccess(`Category '${trimmedName}' updated successfully.`);
      } else {
        // Create Category
        await categoryService.createCategory({
          name: trimmedName,
          description: formData.description.trim() || null,
          is_active: formData.isActive,
        });
        setSuccess(`Category '${trimmedName}' created successfully.`);
      }

      handleCloseModal();
      await loadCategories();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setFormError(
        typeof detail === 'string'
          ? detail
          : 'Failed to save category. Please check your inputs.'
      );
    } finally {
      setFormSubmitting(false);
    }
  };

  // Toggle Active Status
  const handleToggleActive = async (category) => {
    setError('');
    setSuccess('');
    try {
      const newStatus = !category.is_active;
      await categoryService.updateCategory(category.id, {
        is_active: newStatus,
      });
      setSuccess(
        `Category '${category.name}' ${newStatus ? 'activated' : 'deactivated'} successfully.`
      );
      await loadCategories();
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to update category status.'
      );
    }
  };

  // Delete Category
  const handleDelete = async (category) => {
    if (
      !window.confirm(
        `Are you sure you want to permanently delete category '${category.name}'?`
      )
    ) {
      return;
    }

    setError('');
    setSuccess('');
    try {
      await categoryService.deleteCategory(category.id);
      setSuccess(`Category '${category.name}' deleted successfully.`);
      await loadCategories();
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to delete category.'
      );
    }
  };

  return (
    <>
      <AdminNav activeTitle="Categories Management" />
      <div className="container page-wrapper" style={{ paddingTop: 0 }}>
        {/* Header */}
        <div className="page-action-header">
          <div className="page-action-header-left">
            <h1 className="admin-title">Categories Management</h1>
            <p className="admin-subtitle">
              Create, update, and manage product classification categories.
            </p>
          </div>

          <button
          type="button"
          onClick={handleOpenCreate}
          className="btn btn-primary"
        >
          + Add Category
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
          <p>Loading categories...</p>
        </div>
      ) : categories.length === 0 ? (
        <div className="card empty-table-box">
          <h3 className="empty-table-title">No categories yet</h3>
          <p>Click "Add Category" above to create your first product category.</p>
        </div>
      ) : (
        <div className="data-table-wrapper table-responsive-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Category Name</th>
                <th>Slug</th>
                <th>Description</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {categories.map((cat) => (
                <tr key={cat.id}>
                  <td className="table-col-name">{cat.name}</td>
                  <td className="table-col-slug">{cat.slug}</td>
                  <td style={{ color: 'var(--color-text-secondary)' }}>
                    {cat.description || '—'}
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        cat.is_active ? 'badge-active' : 'badge-inactive'
                      }`}
                    >
                      {cat.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="table-actions-cell">
                    <div className="table-action-group">
                      <button
                        type="button"
                        onClick={() => handleOpenEdit(cat)}
                        className="btn btn-outline btn-sm"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => handleToggleActive(cat)}
                        className="btn btn-ghost btn-sm"
                      >
                        {cat.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(cat)}
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
                {editingCategory ? 'Edit Category' : 'Add New Category'}
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
                  <label htmlFor="cat-name" className="form-label">
                    Category Name *
                  </label>
                  <input
                    id="cat-name"
                    type="text"
                    name="name"
                    className="form-input"
                    placeholder="e.g. Graphics Cards"
                    value={formData.name}
                    onChange={handleFormChange}
                    autoFocus
                    required
                    disabled={formSubmitting}
                  />
                  <span className="form-helper">
                    Slug is automatically generated from the category name.
                  </span>
                </div>

                <div className="form-group">
                  <label htmlFor="cat-desc" className="form-label">
                    Description
                  </label>
                  <textarea
                    id="cat-desc"
                    name="description"
                    className="form-input"
                    style={{ height: '80px', padding: '0.5rem 0.75rem', resize: 'vertical' }}
                    placeholder="Optional brief description of products in this category"
                    value={formData.description}
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
                    : editingCategory
                    ? 'Save Changes'
                    : 'Create Category'}
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

export default AdminCategoriesPage;
