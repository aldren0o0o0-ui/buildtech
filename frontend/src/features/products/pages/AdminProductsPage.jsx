import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import productService from '../services/productService';
import productSpecificationService from '../services/productSpecificationService';
import { categoryService, brandService } from '../../catalog';
import ProductSpecificationForm, { resolveHardwareType } from '../components/specifications/ProductSpecificationForm';
import { AdminNav } from '../../admin';

export const AdminProductsPage = () => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Modal State for Product Add / Edit
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState('');
  const [formData, setFormData] = useState({
    sku: '',
    name: '',
    description: '',
    categoryId: '',
    brandId: '',
    price: '',
    imageUrl: '',
    status: 'ACTIVE',
    isActive: true,
  });

  // Modal State for Technical Specifications (Module 4)
  const [isSpecModalOpen, setIsSpecModalOpen] = useState(false);
  const [specProduct, setSpecProduct] = useState(null);
  const [specValues, setSpecValues] = useState({});
  const [specLoading, setSpecLoading] = useState(false);
  const [specSubmitting, setSpecSubmitting] = useState(false);
  const [specError, setSpecError] = useState('');
  const [hasExistingSpec, setHasExistingSpec] = useState(false);

  // Load Categories & Brands for dropdown selectors
  const loadSelectors = useCallback(async () => {
    try {
      const [catData, brandData] = await Promise.all([
        categoryService.listCategories({ include_inactive: true }),
        brandService.listBrands({ include_inactive: true }),
      ]);
      setCategories(catData);
      setBrands(brandData);
    } catch {
      // Ignored non-critical selector load failure
    }
  }, []);

  const loadProducts = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await productService.listProducts({ include_inactive: true });
      setProducts(data);
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Unable to load products list. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSelectors();
    loadProducts();
  }, [loadSelectors, loadProducts]);

  // Open Create Modal
  const handleOpenCreate = () => {
    setEditingProduct(null);
    setFormData({
      sku: '',
      name: '',
      description: '',
      categoryId: categories.length > 0 ? String(categories[0].id) : '',
      brandId: brands.length > 0 ? String(brands[0].id) : '',
      price: '',
      imageUrl: '',
      status: 'ACTIVE',
      isActive: true,
    });
    setFormError('');
    setIsModalOpen(true);
  };

  // Open Edit Modal
  const handleOpenEdit = (product) => {
    setEditingProduct(product);
    setFormData({
      sku: product.sku,
      name: product.name,
      description: product.description || '',
      categoryId: String(product.category_id),
      brandId: String(product.brand_id),
      price: String(product.price),
      imageUrl: product.image_url || '',
      status: product.status,
      isActive: product.is_active,
    });
    setFormError('');
    setIsModalOpen(true);
  };

  // Close Product Modal
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingProduct(null);
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

  // Handle Product Form Submit
  const handleFormSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    const trimmedSku = formData.sku.trim();
    const trimmedName = formData.name.trim();
    const parsedPrice = Number(formData.price);

    if (!trimmedSku) {
      setFormError('Product SKU is required.');
      return;
    }
    if (!trimmedName) {
      setFormError('Product name is required.');
      return;
    }
    if (!formData.categoryId) {
      setFormError('Please select a category.');
      return;
    }
    if (!formData.brandId) {
      setFormError('Please select a brand.');
      return;
    }
    if (isNaN(parsedPrice) || parsedPrice < 0) {
      setFormError('Price must be a valid positive number.');
      return;
    }

    setFormSubmitting(true);
    try {
      if (editingProduct) {
        await productService.updateProduct(editingProduct.id, {
          sku: trimmedSku,
          name: trimmedName,
          description: formData.description.trim() || null,
          category_id: Number(formData.categoryId),
          brand_id: Number(formData.brandId),
          price: parsedPrice,
          image_url: formData.imageUrl.trim() || null,
          status: formData.status,
          is_active: formData.isActive,
        });
        setSuccess(`Product '${trimmedName}' updated successfully.`);
      } else {
        await productService.createProduct({
          sku: trimmedSku,
          name: trimmedName,
          description: formData.description.trim() || null,
          category_id: Number(formData.categoryId),
          brand_id: Number(formData.brandId),
          price: parsedPrice,
          image_url: formData.imageUrl.trim() || null,
          status: formData.status,
          is_active: formData.isActive,
        });
        setSuccess(`Product '${trimmedName}' created successfully.`);
      }

      handleCloseModal();
      await loadProducts();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setFormError(
        typeof detail === 'string'
          ? detail
          : 'Failed to save product. Please verify all fields.'
      );
    } finally {
      setFormSubmitting(false);
    }
  };

  // Toggle Active Status
  const handleToggleActive = async (product) => {
    setError('');
    setSuccess('');
    try {
      const newStatus = !product.is_active;
      await productService.updateProduct(product.id, {
        is_active: newStatus,
      });
      setSuccess(
        `Product '${product.name}' ${newStatus ? 'activated' : 'deactivated'} successfully.`
      );
      await loadProducts();
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to update product status.'
      );
    }
  };

  // Delete Product
  const handleDelete = async (product) => {
    if (
      !window.confirm(
        `Are you sure you want to permanently delete product '${product.name}' (SKU: ${product.sku})?`
      )
    ) {
      return;
    }

    setError('');
    setSuccess('');
    try {
      await productService.deleteProduct(product.id);
      setSuccess(`Product '${product.name}' deleted successfully.`);
      await loadProducts();
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to delete product.'
      );
    }
  };

  // ========================================================
  // MODULE 4: TECHNICAL SPECIFICATIONS MODAL ACTIONS
  // ========================================================

  const handleOpenSpecs = async (product) => {
    setSpecProduct(product);
    setSpecError('');
    setSpecValues({});
    setHasExistingSpec(false);
    setIsSpecModalOpen(true);
    setSpecLoading(true);

    try {
      const response = await productSpecificationService.getSpecifications(product.id, {
        include_inactive: true,
      });
      if (response && response.data) {
        setSpecValues(response.data);
        setHasExistingSpec(true);
      }
    } catch {
      // Not yet configured is normal
    } finally {
      setSpecLoading(false);
    }
  };

  const handleCloseSpecs = () => {
    setIsSpecModalOpen(false);
    setSpecProduct(null);
    setSpecValues({});
    setSpecError('');
  };

  const handleSpecChange = (e) => {
    const { name, value, type, checked } = e.target;
    setSpecValues((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    if (specError) setSpecError('');
  };

  const handleSpecSubmit = async (e) => {
    e.preventDefault();
    if (!specProduct) return;

    setSpecSubmitting(true);
    setSpecError('');
    try {
      await productSpecificationService.upsertSpecifications(specProduct.id, specValues);
      setSuccess(`Technical specifications for '${specProduct.name}' saved successfully.`);
      handleCloseSpecs();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setSpecError(
        typeof detail === 'string'
          ? detail
          : 'Failed to save technical specifications. Please check all required fields.'
      );
    } finally {
      setSpecSubmitting(false);
    }
  };

  const handleSpecDelete = async () => {
    if (!specProduct) return;
    if (!window.confirm(`Delete technical specifications for '${specProduct.name}'?`)) {
      return;
    }

    setSpecSubmitting(true);
    setSpecError('');
    try {
      await productSpecificationService.deleteSpecifications(specProduct.id);
      setSuccess(`Technical specifications for '${specProduct.name}' deleted.`);
      handleCloseSpecs();
    } catch (err) {
      setSpecError(err.response?.data?.detail || 'Failed to delete specifications.');
    } finally {
      setSpecSubmitting(false);
    }
  };

  return (
    <>
      <AdminNav activeTitle="Products Management" />
      <div className="container page-wrapper" style={{ paddingTop: 0 }}>
        {/* Header */}
        <div className="page-action-header">
          <div className="page-action-header-left">
            <h1 className="admin-title">Products Management</h1>
            <p className="admin-subtitle">
              Manage product catalog items, technical specifications, classifications, and publication status.
            </p>
          </div>

          <button
          type="button"
          onClick={handleOpenCreate}
          className="btn btn-primary"
        >
          + Add Product
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
        <div className="spinner-wrapper" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true"></div>
          <p>Loading products...</p>
        </div>
      ) : products.length === 0 ? (
        <div className="card empty-table-box">
          <h3 className="empty-table-title">No products yet</h3>
          <p>Click "Add Product" above to create your first catalog component.</p>
        </div>
      ) : (
        <div className="data-table-wrapper table-responsive-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Product Name</th>
                <th>Category</th>
                <th>Brand</th>
                <th>Price</th>
                <th>Publication Status</th>
                <th>Active</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id}>
                  <td className="table-col-slug" style={{ fontWeight: 600 }}>{p.sku}</td>
                  <td className="table-col-name">
                    <Link to={`/products/${p.slug}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                      {p.name}
                    </Link>
                  </td>
                  <td>
                    <span className="badge badge-customer">{p.category?.name || '—'}</span>
                  </td>
                  <td>
                    <span className="badge badge-subtle">{p.brand?.name || '—'}</span>
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    {Number(p.price).toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        p.status === 'ACTIVE'
                          ? 'badge-active'
                          : p.status === 'DRAFT'
                          ? 'badge-inactive'
                          : 'badge-subtle'
                      }`}
                    >
                      {p.status}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${p.is_active ? 'badge-active' : 'badge-inactive'}`}>
                      {p.is_active ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td className="table-actions-cell">
                    <div className="table-action-group">
                      <button
                        type="button"
                        onClick={() => handleOpenSpecs(p)}
                        className="btn btn-outline btn-sm"
                        title="Manage technical hardware specifications"
                      >
                        Specs
                      </button>
                      <button
                        type="button"
                        onClick={() => handleOpenEdit(p)}
                        className="btn btn-outline btn-sm"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => handleToggleActive(p)}
                        className="btn btn-ghost btn-sm"
                      >
                        {p.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(p)}
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

      {/* Add / Edit Product Modal */}
      {isModalOpen && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal-card" style={{ maxWidth: '620px' }}>
            <div className="modal-header">
              <h2 className="modal-title">
                {editingProduct ? 'Edit Product' : 'Add New Product'}
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

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="prod-sku" className="form-label">
                      Product SKU *
                    </label>
                    <input
                      id="prod-sku"
                      type="text"
                      name="sku"
                      className="form-input"
                      placeholder="e.g. GPU-4070-SUP"
                      value={formData.sku}
                      onChange={handleFormChange}
                      required
                      disabled={formSubmitting}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="prod-price" className="form-label">
                      Price ($ USD) *
                    </label>
                    <input
                      id="prod-price"
                      type="number"
                      step="0.01"
                      min="0"
                      name="price"
                      className="form-input"
                      placeholder="599.99"
                      value={formData.price}
                      onChange={handleFormChange}
                      required
                      disabled={formSubmitting}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="prod-name" className="form-label">
                    Product Name *
                  </label>
                  <input
                    id="prod-name"
                    type="text"
                    name="name"
                    className="form-input"
                    placeholder="e.g. ASUS ROG Strix GeForce RTX 4070 Super"
                    value={formData.name}
                    onChange={handleFormChange}
                    required
                    disabled={formSubmitting}
                  />
                  <span className="form-helper">
                    Product URL slug is automatically generated from name.
                  </span>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="prod-cat" className="form-label">
                      Category *
                    </label>
                    <select
                      id="prod-cat"
                      name="categoryId"
                      className="form-input"
                      value={formData.categoryId}
                      onChange={handleFormChange}
                      required
                      disabled={formSubmitting}
                    >
                      <option value="">Select Category</option>
                      {categories.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.name} {!cat.is_active && '(Inactive)'}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="prod-brand" className="form-label">
                      Brand *
                    </label>
                    <select
                      id="prod-brand"
                      name="brandId"
                      className="form-input"
                      value={formData.brandId}
                      onChange={handleFormChange}
                      required
                      disabled={formSubmitting}
                    >
                      <option value="">Select Brand</option>
                      {brands.map((b) => (
                        <option key={b.id} value={b.id}>
                          {b.name} {!b.is_active && '(Inactive)'}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="prod-desc" className="form-label">
                    Description
                  </label>
                  <textarea
                    id="prod-desc"
                    name="description"
                    className="form-input"
                    style={{ height: '80px', padding: '0.5rem 0.75rem', resize: 'vertical' }}
                    placeholder="Component overview and highlights"
                    value={formData.description}
                    onChange={handleFormChange}
                    disabled={formSubmitting}
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="prod-image" className="form-label">
                      Image URL
                    </label>
                    <input
                      id="prod-image"
                      type="url"
                      name="imageUrl"
                      className="form-input"
                      placeholder="https://example.com/item.png (optional)"
                      value={formData.imageUrl}
                      onChange={handleFormChange}
                      disabled={formSubmitting}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="prod-status" className="form-label">
                      Publication Status
                    </label>
                    <select
                      id="prod-status"
                      name="status"
                      className="form-input"
                      value={formData.status}
                      onChange={handleFormChange}
                      disabled={formSubmitting}
                    >
                      <option value="ACTIVE">ACTIVE (Published)</option>
                      <option value="DRAFT">DRAFT (Hidden)</option>
                      <option value="ARCHIVED">ARCHIVED (Retired)</option>
                    </select>
                  </div>
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
                    Operational Active (enabled in store)
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
                    : editingProduct
                    ? 'Save Changes'
                    : 'Create Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Module 4: Technical Specifications Modal */}
      {isSpecModalOpen && specProduct && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal-card" style={{ maxWidth: '680px' }}>
            <div className="modal-header">
              <div>
                <h2 className="modal-title">Technical Specifications</h2>
                <p className="card-description" style={{ margin: 0 }}>
                  {specProduct.name} ({specProduct.sku})
                </p>
              </div>
              <button
                type="button"
                onClick={handleCloseSpecs}
                className="modal-close-btn"
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSpecSubmit} noValidate>
              <div className="modal-body">
                {specError && (
                  <div className="alert alert-danger" role="alert">
                    <span>{specError}</span>
                  </div>
                )}

                {specLoading ? (
                  <div className="spinner-wrapper" style={{ minHeight: '200px' }}>
                    <div className="spinner"></div>
                    <p>Loading specifications...</p>
                  </div>
                ) : (
                  <ProductSpecificationForm
                    category={specProduct.category}
                    values={specValues}
                    onChange={handleSpecChange}
                    disabled={specSubmitting}
                  />
                )}
              </div>

              <div className="modal-footer" style={{ justifyContent: 'space-between' }}>
                <div>
                  {hasExistingSpec && (
                    <button
                      type="button"
                      onClick={handleSpecDelete}
                      className="btn btn-ghost"
                      style={{ color: 'var(--color-danger)' }}
                      disabled={specSubmitting || specLoading}
                    >
                      Delete Specifications
                    </button>
                  )}
                </div>

                <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                  <button
                    type="button"
                    onClick={handleCloseSpecs}
                    className="btn btn-outline"
                    disabled={specSubmitting}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={specSubmitting || specLoading || !resolveHardwareType(specProduct.category)}
                  >
                    {specSubmitting ? 'Saving...' : 'Save Specifications'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
      </div>
    </>
  );
};

export default AdminProductsPage;
