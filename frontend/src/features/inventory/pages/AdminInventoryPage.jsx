import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import inventoryService from '../services/inventoryService';
import AvailabilityBadge from '../components/AvailabilityBadge';
import StockInForm from '../components/StockInForm';
import InventoryAdjustmentForm from '../components/InventoryAdjustmentForm';
import InventoryHistory from '../components/InventoryHistory';
import { AdminNav } from '../../admin';

export const AdminInventoryPage = () => {
  const [inventories, setInventories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Filters
  const [search, setSearch] = useState('');
  const [availabilityFilter, setAvailabilityFilter] = useState('');
  const [sortBy, setSortBy] = useState('name_asc');

  // Modals
  const [activeModal, setActiveModal] = useState(null); // 'STOCK_IN', 'ADJUST', 'HISTORY', 'THRESHOLD'
  const [selectedItem, setSelectedItem] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [actionSubmitting, setActionSubmitting] = useState(false);
  const [modalError, setModalError] = useState('');

  // Threshold form state
  const [newThreshold, setNewThreshold] = useState('');

  const loadInventories = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (availabilityFilter) params.availability = availabilityFilter;
      if (sortBy) params.sort = sortBy;

      const data = await inventoryService.listInventory(params);
      setInventories(data);
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Failed to load inventory data. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  }, [search, availabilityFilter, sortBy]);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadInventories();
    }, 200);
    return () => clearTimeout(timer);
  }, [loadInventories]);

  // Modal Handlers
  const handleOpenStockIn = (item) => {
    setSelectedItem(item);
    setModalError('');
    setActiveModal('STOCK_IN');
  };

  const handleOpenAdjust = (item) => {
    setSelectedItem(item);
    setModalError('');
    setActiveModal('ADJUST');
  };

  const handleOpenHistory = async (item) => {
    setSelectedItem(item);
    setActiveModal('HISTORY');
    setHistoryLoading(true);
    try {
      const txs = await inventoryService.getTransactions(item.product_id);
      setTransactions(txs);
    } catch {
      setTransactions([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleOpenThreshold = (item) => {
    setSelectedItem(item);
    setNewThreshold(String(item.low_stock_threshold));
    setModalError('');
    setActiveModal('THRESHOLD');
  };

  const handleCloseModal = () => {
    setActiveModal(null);
    setSelectedItem(null);
    setTransactions([]);
    setModalError('');
  };

  // Stock In Submit
  const handleStockInSubmit = async (payload) => {
    setActionSubmitting(true);
    setModalError('');
    try {
      await inventoryService.stockIn(selectedItem.product_id, payload);
      setSuccess(`Added ${payload.quantity} units to '${selectedItem.product?.name}'.`);
      handleCloseModal();
      await loadInventories();
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to complete stock-in.');
    } finally {
      setActionSubmitting(false);
    }
  };

  // Adjustment Submit
  const handleAdjustSubmit = async (payload) => {
    setActionSubmitting(true);
    setModalError('');
    try {
      await inventoryService.adjustInventory(selectedItem.product_id, payload);
      setSuccess(
        `Adjusted stock for '${selectedItem.product?.name}' (${payload.type === 'ADJUSTMENT_IN' ? '+' : '-'}${payload.quantity}).`
      );
      handleCloseModal();
      await loadInventories();
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to complete stock adjustment.');
    } finally {
      setActionSubmitting(false);
    }
  };

  // Threshold Submit
  const handleThresholdSubmit = async (e) => {
    e.preventDefault();
    const val = parseInt(newThreshold, 10);
    if (isNaN(val) || val < 0) {
      setModalError('Threshold must be a non-negative integer (>= 0).');
      return;
    }

    setActionSubmitting(true);
    setModalError('');
    try {
      await inventoryService.updateThreshold(selectedItem.product_id, {
        low_stock_threshold: val,
      });
      setSuccess(`Updated low stock threshold for '${selectedItem.product?.name}' to ${val}.`);
      handleCloseModal();
      await loadInventories();
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to update threshold.');
    } finally {
      setActionSubmitting(false);
    }
  };

  return (
    <>
      <AdminNav activeTitle="Inventory Management" />
      <div className="container page-wrapper" style={{ paddingTop: 0 }}>
        {/* Action Header */}
        <div className="page-action-header">
          <div className="page-action-header-left">
            <h1 className="admin-title">Inventory Management</h1>
            <p className="admin-subtitle">
              Authoritative stock levels, physical receiving, audit adjustments, and low-stock threshold management.
            </p>
          </div>
        </div>

      {/* Global Alerts */}
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

      {/* Filter Toolbar */}
      <div className="filter-toolbar">
        <div className="filter-item-search">
          <label htmlFor="inv-search" className="filter-label">Search Product / SKU</label>
          <input
            id="inv-search"
            type="text"
            className="form-input"
            placeholder="Search by product name or SKU..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="filter-item">
          <label htmlFor="inv-avail" className="filter-label">Availability Status</label>
          <select
            id="inv-avail"
            className="form-input"
            value={availabilityFilter}
            onChange={(e) => setAvailabilityFilter(e.target.value)}
          >
            <option value="">All Stock States</option>
            <option value="IN_STOCK">In Stock</option>
            <option value="LOW_STOCK">Low Stock</option>
            <option value="OUT_OF_STOCK">Out of Stock</option>
          </select>
        </div>

        <div className="filter-item">
          <label htmlFor="inv-sort" className="filter-label">Sort By</label>
          <select
            id="inv-sort"
            className="form-input"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="name_asc">Product Name (A-Z)</option>
            <option value="name_desc">Product Name (Z-A)</option>
            <option value="available_desc">Available (Highest First)</option>
            <option value="available_asc">Available (Lowest First)</option>
            <option value="quantity_desc">Total Stock (Highest First)</option>
          </select>
        </div>

        <div className="filter-item-action">
          <button
            type="button"
            onClick={() => {
              setSearch('');
              setAvailabilityFilter('');
              setSortBy('name_asc');
            }}
            className="btn btn-outline btn-sm"
            style={{ height: '38px', marginTop: 'auto' }}
          >
            Reset
          </button>
        </div>
      </div>

      {/* Main Table */}
      {loading ? (
        <div className="spinner-wrapper" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true"></div>
          <p>Loading inventory data...</p>
        </div>
      ) : inventories.length === 0 ? (
        <div className="card empty-table-box">
          <h3 className="empty-table-title">No matching products found</h3>
          <p>Create products in the Products Catalog to begin tracking stock.</p>
        </div>
      ) : (
        <div className="data-table-wrapper table-responsive-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Product Name</th>
                <th>Total Stock</th>
                <th>Reserved</th>
                <th>Available</th>
                <th>Status</th>
                <th>Alert Threshold</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {inventories.map((item) => (
                <tr key={item.id}>
                  <td className="table-col-slug" style={{ fontWeight: 600 }}>
                    {item.product?.sku}
                  </td>
                  <td className="table-col-name">
                    <Link
                      to={`/products/${item.product?.id}`}
                      style={{ color: 'inherit', textDecoration: 'none' }}
                    >
                      {item.product?.name}
                    </Link>
                  </td>
                  <td style={{ fontWeight: 600 }}>{item.quantity}</td>
                  <td style={{ color: 'var(--color-text-secondary)' }}>
                    {item.reserved_quantity}
                  </td>
                  <td style={{ fontWeight: 700, color: item.available_quantity > 0 ? 'var(--color-text)' : 'var(--color-danger)' }}>
                    {item.available_quantity}
                  </td>
                  <td>
                    <AvailabilityBadge status={item.availability_status} />
                  </td>
                  <td>
                    <button
                      type="button"
                      onClick={() => handleOpenThreshold(item)}
                      className="btn btn-ghost btn-sm"
                      style={{ padding: '0.125rem 0.375rem', fontSize: '0.8125rem' }}
                      title="Click to edit threshold"
                    >
                      {item.low_stock_threshold} units
                    </button>
                  </td>
                  <td className="table-actions-cell">
                    <div className="table-action-group">
                      <button
                        type="button"
                        onClick={() => handleOpenStockIn(item)}
                        className="btn btn-outline btn-sm"
                      >
                        Stock In
                      </button>
                      <button
                        type="button"
                        onClick={() => handleOpenAdjust(item)}
                        className="btn btn-outline btn-sm"
                      >
                        Adjust
                      </button>
                      <button
                        type="button"
                        onClick={() => handleOpenHistory(item)}
                        className="btn btn-ghost btn-sm"
                      >
                        History
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Stock In Modal */}
      {activeModal === 'STOCK_IN' && selectedItem && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal-card">
            <div className="modal-header">
              <h2 className="modal-title">Receive Stock (Stock In)</h2>
              <button
                type="button"
                onClick={handleCloseModal}
                className="modal-close-btn"
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>
            <StockInForm
              item={selectedItem}
              onSubmit={handleStockInSubmit}
              onCancel={handleCloseModal}
              submitting={actionSubmitting}
            />
          </div>
        </div>
      )}

      {/* Adjustment Modal */}
      {activeModal === 'ADJUST' && selectedItem && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal-card">
            <div className="modal-header">
              <h2 className="modal-title">Inventory Adjustment</h2>
              <button
                type="button"
                onClick={handleCloseModal}
                className="modal-close-btn"
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>
            <InventoryAdjustmentForm
              item={selectedItem}
              onSubmit={handleAdjustSubmit}
              onCancel={handleCloseModal}
              submitting={actionSubmitting}
            />
          </div>
        </div>
      )}

      {/* History Modal */}
      {activeModal === 'HISTORY' && selectedItem && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal-card" style={{ maxWidth: '680px' }}>
            <div className="modal-header">
              <div>
                <h2 className="modal-title">Transaction History</h2>
                <p className="card-description" style={{ margin: 0 }}>
                  {selectedItem.product?.name} ({selectedItem.product?.sku})
                </p>
              </div>
              <button
                type="button"
                onClick={handleCloseModal}
                className="modal-close-btn"
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>
            <InventoryHistory
              transactions={transactions}
              loading={historyLoading}
              onClose={handleCloseModal}
            />
          </div>
        </div>
      )}

      {/* Threshold Modal */}
      {activeModal === 'THRESHOLD' && selectedItem && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal-card">
            <div className="modal-header">
              <h2 className="modal-title">Low Stock Alert Threshold</h2>
              <button
                type="button"
                onClick={handleCloseModal}
                className="modal-close-btn"
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleThresholdSubmit} noValidate>
              <div className="modal-body">
                {modalError && (
                  <div className="alert alert-danger" role="alert">
                    <span>{modalError}</span>
                  </div>
                )}
                <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-4)' }}>
                  Set the minimum available unit count for <strong>{selectedItem.product?.name}</strong> before it transitions to <strong>LOW_STOCK</strong> status.
                </p>
                <div className="form-group">
                  <label htmlFor="thresh-val" className="form-label">
                    Alert Threshold (Units) *
                  </label>
                  <input
                    id="thresh-val"
                    type="number"
                    min="0"
                    className="form-input"
                    value={newThreshold}
                    onChange={(e) => setNewThreshold(e.target.value)}
                    required
                    disabled={actionSubmitting}
                    autoFocus
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="btn btn-outline"
                  disabled={actionSubmitting}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={actionSubmitting}
                >
                  {actionSubmitting ? 'Saving...' : 'Save Threshold'}
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

export default AdminInventoryPage;
