import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import productService from '../services/productService';
import { categoryService, brandService } from '../../catalog';
import ProductCard from '../components/ProductCard';

export const ProductsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // Master catalog state
  const [products, setProducts] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Dropdown / filter options from database
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);

  // Mobile drawer state
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);

  // Read URL query params
  const searchParam = searchParams.get('search') || '';
  const categoryParam = searchParams.get('category') || searchParams.get('category_id') || '';
  const brandParam = searchParams.get('brand') || searchParams.get('brand_id') || '';
  const minPriceParam = searchParams.get('min_price') || '';
  const maxPriceParam = searchParams.get('max_price') || '';
  const inStockParam = searchParams.get('in_stock') === 'true';
  const sortParam = searchParams.get('sort') || 'newest';
  const pageParam = parseInt(searchParams.get('page') || '1', 10);

  // Specification URL params
  const socketParam = searchParams.get('socket') || '';
  const coresMinParam = searchParams.get('cores_min') || '';
  const vramMinParam = searchParams.get('vram_min') || '';
  const formFactorParam = searchParams.get('form_factor') || '';
  const memoryTypeParam = searchParams.get('memory_type') || '';
  const capacityMinParam = searchParams.get('capacity_min') || '';
  const storageTypeParam = searchParams.get('storage_type') || '';
  const wattageMinParam = searchParams.get('wattage_min') || '';
  const caseTypeParam = searchParams.get('case_type') || '';
  const coolerTypeParam = searchParams.get('cooler_type') || '';

  // Local state for search text input to allow smooth typing before debounce
  const [searchInput, setSearchInput] = useState(searchParam);

  // Synchronize search input if URL changes externally
  useEffect(() => {
    setSearchInput(searchParam);
  }, [searchParam]);

  // Load initial Categories & Brands
  useEffect(() => {
    const loadFilterOptions = async () => {
      try {
        const [catData, brandData] = await Promise.all([
          categoryService.listCategories(),
          brandService.listBrands(),
        ]);
        setCategories(catData || []);
        setBrands(brandData || []);
      } catch {
        // Non-blocking for catalog display
      }
    };
    loadFilterOptions();
  }, []);

  // Generic helper to update URL search parameters
  const updateFilters = useCallback(
    (updates, resetPage = true) => {
      setSearchParams((prevParams) => {
        const newParams = new URLSearchParams(prevParams);

        Object.entries(updates).forEach(([key, value]) => {
          if (value === null || value === undefined || value === '' || value === false) {
            newParams.delete(key);
          } else {
            newParams.set(key, String(value));
          }
        });

        if (resetPage && !('page' in updates)) {
          newParams.delete('page');
        }

        return newParams;
      });
    },
    [setSearchParams]
  );

  // Debounce search text input
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== searchParam) {
        updateFilters({ search: searchInput.trim() || null });
      }
    }, 350);
    return () => clearTimeout(timer);
  }, [searchInput, searchParam, updateFilters]);

  // Fetch products whenever URL parameters change
  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const params = {
        page: pageParam,
        page_size: 12,
        sort: sortParam,
      };

      if (searchParam) params.search = searchParam;
      if (categoryParam) {
        if (/^\d+$/.test(categoryParam)) {
          params.category_id = parseInt(categoryParam, 10);
        } else {
          params.category = categoryParam;
        }
      }
      if (brandParam) {
        if (/^\d+$/.test(brandParam)) {
          params.brand_id = parseInt(brandParam, 10);
        } else {
          params.brand = brandParam;
        }
      }
      if (minPriceParam && !isNaN(Number(minPriceParam))) {
        params.min_price = Number(minPriceParam);
      }
      if (maxPriceParam && !isNaN(Number(maxPriceParam))) {
        params.max_price = Number(maxPriceParam);
      }
      if (inStockParam) params.in_stock = true;

      // Specification parameters
      if (socketParam) params.socket = socketParam;
      if (coresMinParam) params.cores_min = parseInt(coresMinParam, 10);
      if (vramMinParam) params.vram_min = parseInt(vramMinParam, 10);
      if (formFactorParam) params.form_factor = formFactorParam;
      if (memoryTypeParam) params.memory_type = memoryTypeParam;
      if (capacityMinParam) params.capacity_min = parseInt(capacityMinParam, 10);
      if (storageTypeParam) params.storage_type = storageTypeParam;
      if (wattageMinParam) params.wattage_min = parseInt(wattageMinParam, 10);
      if (caseTypeParam) params.case_type = caseTypeParam;
      if (coolerTypeParam) params.cooler_type = coolerTypeParam;

      const response = await productService.listProducts(params);

      if (response && Array.isArray(response.items)) {
        setProducts(response.items);
        setTotalCount(response.total);
        setTotalPages(response.total_pages || response.pages || 1);
      } else if (Array.isArray(response)) {
        setProducts(response);
        setTotalCount(response.length);
        setTotalPages(1);
      } else {
        setProducts([]);
        setTotalCount(0);
        setTotalPages(1);
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          'Unable to load catalog products. Please check your connection and try again.'
      );
    } finally {
      setLoading(false);
    }
  }, [
    searchParam,
    categoryParam,
    brandParam,
    minPriceParam,
    maxPriceParam,
    inStockParam,
    socketParam,
    coresMinParam,
    vramMinParam,
    formFactorParam,
    memoryTypeParam,
    capacityMinParam,
    storageTypeParam,
    wattageMinParam,
    caseTypeParam,
    coolerTypeParam,
    sortParam,
    pageParam,
  ]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  // Determine active category object and its classification
  const activeCategoryObj = useMemo(() => {
    if (!categoryParam) return null;
    return categories.find(
      (c) => String(c.id) === String(categoryParam) || c.slug === categoryParam
    );
  }, [categories, categoryParam]);

  const categoryType = useMemo(() => {
    if (!activeCategoryObj) return '';
    const slug = (activeCategoryObj.slug || '').toLowerCase();
    const name = (activeCategoryObj.name || '').toLowerCase();
    if (slug.includes('cpu') || name.includes('processor')) return 'cpu';
    if (slug.includes('gpu') || name.includes('graphic')) return 'gpu';
    if (slug.includes('motherboard')) return 'motherboard';
    if (slug.includes('memory') || slug.includes('ram')) return 'memory';
    if (slug.includes('storage') || slug.includes('ssd')) return 'storage';
    if (slug.includes('psu') || name.includes('power')) return 'psu';
    if (slug.includes('case')) return 'case';
    if (slug.includes('cooling') || name.includes('cooler')) return 'cooling';
    return '';
  }, [activeCategoryObj]);

  // Active filter count and removable chips list
  const activeFilters = useMemo(() => {
    const list = [];
    if (searchParam) {
      list.push({ key: 'search', label: `Search: "${searchParam}"`, onRemove: () => updateFilters({ search: null }) });
    }
    if (categoryParam && activeCategoryObj) {
      list.push({
        key: 'category',
        label: `Category: ${activeCategoryObj.name}`,
        onRemove: () => updateFilters({
          category: null,
          category_id: null,
          socket: null,
          cores_min: null,
          vram_min: null,
          form_factor: null,
          memory_type: null,
          capacity_min: null,
          storage_type: null,
          wattage_min: null,
          case_type: null,
          cooler_type: null,
        }),
      });
    }
    if (brandParam) {
      const bObj = brands.find((b) => String(b.id) === String(brandParam) || b.slug === brandParam);
      list.push({
        key: 'brand',
        label: `Brand: ${bObj ? bObj.name : brandParam}`,
        onRemove: () => updateFilters({ brand: null, brand_id: null }),
      });
    }
    if (minPriceParam || maxPriceParam) {
      const minStr = minPriceParam ? `$${minPriceParam}` : '$0';
      const maxStr = maxPriceParam ? `$${maxPriceParam}` : 'Any';
      list.push({
        key: 'price',
        label: `Price: ${minStr} – ${maxStr}`,
        onRemove: () => updateFilters({ min_price: null, max_price: null }),
      });
    }
    if (inStockParam) {
      list.push({
        key: 'in_stock',
        label: 'In Stock Only',
        onRemove: () => updateFilters({ in_stock: null }),
      });
    }
    if (socketParam) {
      list.push({
        key: 'socket',
        label: `Socket: ${socketParam}`,
        onRemove: () => updateFilters({ socket: null }),
      });
    }
    if (coresMinParam) {
      list.push({
        key: 'cores_min',
        label: `${coresMinParam}+ Cores`,
        onRemove: () => updateFilters({ cores_min: null }),
      });
    }
    if (vramMinParam) {
      list.push({
        key: 'vram_min',
        label: `${vramMinParam}GB+ VRAM`,
        onRemove: () => updateFilters({ vram_min: null }),
      });
    }
    if (formFactorParam) {
      list.push({
        key: 'form_factor',
        label: `Form Factor: ${formFactorParam}`,
        onRemove: () => updateFilters({ form_factor: null }),
      });
    }
    if (memoryTypeParam) {
      list.push({
        key: 'memory_type',
        label: `Memory: ${memoryTypeParam}`,
        onRemove: () => updateFilters({ memory_type: null }),
      });
    }
    if (capacityMinParam) {
      list.push({
        key: 'capacity_min',
        label: `${capacityMinParam}GB+ Capacity`,
        onRemove: () => updateFilters({ capacity_min: null }),
      });
    }
    if (storageTypeParam) {
      list.push({
        key: 'storage_type',
        label: `Storage: ${storageTypeParam}`,
        onRemove: () => updateFilters({ storage_type: null }),
      });
    }
    if (wattageMinParam) {
      list.push({
        key: 'wattage_min',
        label: `${wattageMinParam}W+ Power`,
        onRemove: () => updateFilters({ wattage_min: null }),
      });
    }
    if (caseTypeParam) {
      list.push({
        key: 'case_type',
        label: `Case: ${caseTypeParam}`,
        onRemove: () => updateFilters({ case_type: null }),
      });
    }
    if (coolerTypeParam) {
      list.push({
        key: 'cooler_type',
        label: `Cooler: ${coolerTypeParam}`,
        onRemove: () => updateFilters({ cooler_type: null }),
      });
    }
    return list;
  }, [
    searchParam,
    categoryParam,
    activeCategoryObj,
    brandParam,
    brands,
    minPriceParam,
    maxPriceParam,
    inStockParam,
    socketParam,
    coresMinParam,
    vramMinParam,
    formFactorParam,
    memoryTypeParam,
    capacityMinParam,
    storageTypeParam,
    wattageMinParam,
    caseTypeParam,
    coolerTypeParam,
    updateFilters,
  ]);

  const clearAllFilters = () => {
    setSearchInput('');
    setSearchParams(new URLSearchParams());
  };

  // Render Filter Sidebar content
  const renderFilterSidebar = () => (
    <div className="storefront-filters-sidebar">
      {/* Category Section */}
      <div className="filter-group">
        <h3 className="filter-group-title">Category</h3>
        <div className="filter-options-list">
          <label className={`filter-radio-label ${!categoryParam ? 'active' : ''}`}>
            <input
              type="radio"
              name="category_filter"
              checked={!categoryParam}
              onChange={() =>
                updateFilters({
                  category: null,
                  category_id: null,
                  socket: null,
                  cores_min: null,
                  vram_min: null,
                  form_factor: null,
                  memory_type: null,
                  capacity_min: null,
                  storage_type: null,
                  wattage_min: null,
                  case_type: null,
                  cooler_type: null,
                })
              }
            />
            <span>All Categories</span>
          </label>
          {categories.map((cat) => (
            <label
              key={cat.id}
              className={`filter-radio-label ${
                categoryParam === cat.slug || String(categoryParam) === String(cat.id)
                  ? 'active'
                  : ''
              }`}
            >
              <input
                type="radio"
                name="category_filter"
                checked={categoryParam === cat.slug || String(categoryParam) === String(cat.id)}
                onChange={() =>
                  updateFilters({
                    category: cat.slug,
                    category_id: null,
                    socket: null,
                    cores_min: null,
                    vram_min: null,
                    form_factor: null,
                    memory_type: null,
                    capacity_min: null,
                    storage_type: null,
                    wattage_min: null,
                    case_type: null,
                    cooler_type: null,
                  })
                }
              />
              <span>{cat.name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Brand Section */}
      <div className="filter-group">
        <h3 className="filter-group-title">Brand</h3>
        <div className="filter-options-list">
          <label className={`filter-radio-label ${!brandParam ? 'active' : ''}`}>
            <input
              type="radio"
              name="brand_filter"
              checked={!brandParam}
              onChange={() => updateFilters({ brand: null, brand_id: null })}
            />
            <span>All Brands</span>
          </label>
          {brands.map((b) => (
            <label
              key={b.id}
              className={`filter-radio-label ${
                brandParam === b.slug || String(brandParam) === String(b.id) ? 'active' : ''
              }`}
            >
              <input
                type="radio"
                name="brand_filter"
                checked={brandParam === b.slug || String(brandParam) === String(b.id)}
                onChange={() => updateFilters({ brand: b.slug, brand_id: null })}
              />
              <span>{b.name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Price Filter */}
      <div className="filter-group">
        <h3 className="filter-group-title">Price Range ($)</h3>
        <div className="filter-price-inputs">
          <input
            type="number"
            min="0"
            className="form-input form-input-sm"
            placeholder="Min"
            value={minPriceParam}
            onChange={(e) => updateFilters({ min_price: e.target.value || null })}
          />
          <span className="filter-price-separator">–</span>
          <input
            type="number"
            min="0"
            className="form-input form-input-sm"
            placeholder="Max"
            value={maxPriceParam}
            onChange={(e) => updateFilters({ max_price: e.target.value || null })}
          />
        </div>
      </div>

      {/* Availability Filter */}
      <div className="filter-group">
        <h3 className="filter-group-title">Availability</h3>
        <label className="filter-checkbox-label">
          <input
            type="checkbox"
            checked={inStockParam}
            onChange={(e) => updateFilters({ in_stock: e.target.checked ? 'true' : null })}
          />
          <span>In Stock Only</span>
        </label>
      </div>

      {/* Dynamic Category-Specific Specification Filters */}
      {categoryType === 'cpu' && (
        <div className="filter-group spec-filter-box">
          <h3 className="filter-group-title">Processor Specs</h3>
          <div className="spec-subgroup">
            <span className="spec-subgroup-label">Socket</span>
            <div className="filter-pill-selector">
              {['AM5', 'AM4', 'LGA1700', 'LGA1200'].map((sock) => (
                <button
                  key={sock}
                  type="button"
                  className={`spec-pill-btn ${socketParam === sock ? 'active' : ''}`}
                  onClick={() => updateFilters({ socket: socketParam === sock ? null : sock })}
                >
                  {sock}
                </button>
              ))}
            </div>
          </div>
          <div className="spec-subgroup">
            <span className="spec-subgroup-label">Min Cores</span>
            <div className="filter-pill-selector">
              {[6, 8, 12, 16].map((num) => (
                <button
                  key={num}
                  type="button"
                  className={`spec-pill-btn ${coresMinParam === String(num) ? 'active' : ''}`}
                  onClick={() =>
                    updateFilters({ cores_min: coresMinParam === String(num) ? null : num })
                  }
                >
                  {num}+
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {categoryType === 'gpu' && (
        <div className="filter-group spec-filter-box">
          <h3 className="filter-group-title">Graphics Specs</h3>
          <div className="spec-subgroup">
            <span className="spec-subgroup-label">Min VRAM</span>
            <div className="filter-pill-selector">
              {[8, 12, 16, 24].map((vram) => (
                <button
                  key={vram}
                  type="button"
                  className={`spec-pill-btn ${vramMinParam === String(vram) ? 'active' : ''}`}
                  onClick={() =>
                    updateFilters({ vram_min: vramMinParam === String(vram) ? null : vram })
                  }
                >
                  {vram} GB
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {categoryType === 'motherboard' && (
        <div className="filter-group spec-filter-box">
          <h3 className="filter-group-title">Motherboard Specs</h3>
          <div className="spec-subgroup">
            <span className="spec-subgroup-label">Socket</span>
            <div className="filter-pill-selector">
              {['AM5', 'AM4', 'LGA1700'].map((sock) => (
                <button
                  key={sock}
                  type="button"
                  className={`spec-pill-btn ${socketParam === sock ? 'active' : ''}`}
                  onClick={() => updateFilters({ socket: socketParam === sock ? null : sock })}
                >
                  {sock}
                </button>
              ))}
            </div>
          </div>
          <div className="spec-subgroup">
            <span className="spec-subgroup-label">Form Factor</span>
            <div className="filter-pill-selector">
              {['ATX', 'Micro-ATX', 'Mini-ITX'].map((ff) => (
                <button
                  key={ff}
                  type="button"
                  className={`spec-pill-btn ${formFactorParam === ff ? 'active' : ''}`}
                  onClick={() => updateFilters({ form_factor: formFactorParam === ff ? null : ff })}
                >
                  {ff}
                </button>
              ))}
            </div>
          </div>
          <div className="spec-subgroup">
            <span className="spec-subgroup-label">Memory Type</span>
            <div className="filter-pill-selector">
              {['DDR5', 'DDR4'].map((mt) => (
                <button
                  key={mt}
                  type="button"
                  className={`spec-pill-btn ${memoryTypeParam === mt ? 'active' : ''}`}
                  onClick={() => updateFilters({ memory_type: memoryTypeParam === mt ? null : mt })}
                >
                  {mt}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {categoryType === 'memory' && (
        <div className="filter-group spec-filter-box">
          <h3 className="filter-group-title">Memory Specs</h3>
          <div className="spec-subgroup">
            <span className="spec-subgroup-label">Type</span>
            <div className="filter-pill-selector">
              {['DDR5', 'DDR4'].map((mt) => (
                <button
                  key={mt}
                  type="button"
                  className={`spec-pill-btn ${memoryTypeParam === mt ? 'active' : ''}`}
                  onClick={() => updateFilters({ memory_type: memoryTypeParam === mt ? null : mt })}
                >
                  {mt}
                </button>
              ))}
            </div>
          </div>
          <div className="spec-subgroup">
            <span className="spec-subgroup-label">Min Capacity</span>
            <div className="filter-pill-selector">
              {[16, 32, 64].map((cap) => (
                <button
                  key={cap}
                  type="button"
                  className={`spec-pill-btn ${capacityMinParam === String(cap) ? 'active' : ''}`}
                  onClick={() =>
                    updateFilters({ capacity_min: capacityMinParam === String(cap) ? null : cap })
                  }
                >
                  {cap} GB
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {categoryType === 'storage' && (
        <div className="filter-group spec-filter-box">
          <h3 className="filter-group-title">Storage Specs</h3>
          <div className="spec-subgroup">
            <span className="spec-subgroup-label">Storage Type</span>
            <div className="filter-pill-selector">
              {['NVMe SSD', 'SATA SSD'].map((st) => (
                <button
                  key={st}
                  type="button"
                  className={`spec-pill-btn ${storageTypeParam === st ? 'active' : ''}`}
                  onClick={() => updateFilters({ storage_type: storageTypeParam === st ? null : st })}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {categoryType === 'psu' && (
        <div className="filter-group spec-filter-box">
          <h3 className="filter-group-title">Power Supply Specs</h3>
          <div className="spec-subgroup">
            <span className="spec-subgroup-label">Min Wattage</span>
            <div className="filter-pill-selector">
              {[650, 750, 850, 1000].map((w) => (
                <button
                  key={w}
                  type="button"
                  className={`spec-pill-btn ${wattageMinParam === String(w) ? 'active' : ''}`}
                  onClick={() =>
                    updateFilters({ wattage_min: wattageMinParam === String(w) ? null : w })
                  }
                >
                  {w}W
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Clear All Action in sidebar */}
      {activeFilters.length > 0 && (
        <button
          type="button"
          onClick={clearAllFilters}
          className="btn btn-ghost btn-sm btn-block"
          style={{ marginTop: 'var(--space-4)' }}
        >
          Reset All Filters
        </button>
      )}
    </div>
  );

  return (
    <div className="container page-wrapper">
      {/* Prominent Storefront Search Bar */}
      <div className="storefront-search-section">
        <div className="storefront-search-container">
          <span className="storefront-search-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </span>
          <input
            id="storefront-product-search"
            type="text"
            className="storefront-search-input"
            placeholder="Search processors, graphics cards, motherboards, memory, power supplies..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            aria-label="Search products"
          />
          {searchInput && (
            <button
              type="button"
              className="storefront-search-clear-btn"
              onClick={() => {
                setSearchInput('');
                updateFilters({ search: null });
              }}
              aria-label="Clear search text"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="storefront-catalog-layout">
        {/* Desktop Sidebar */}
        <aside className="storefront-sidebar-desktop" aria-label="Catalog Filters">
          <div className="storefront-sidebar-header">
            <h2>Filters</h2>
            {activeFilters.length > 0 && (
              <button
                type="button"
                onClick={clearAllFilters}
                className="filter-clear-all-link"
              >
                Clear all
              </button>
            )}
          </div>
          {renderFilterSidebar()}
        </aside>

        {/* Mobile Filter Drawer */}
        {mobileFiltersOpen && (
          <div className="mobile-filter-modal-overlay" onClick={() => setMobileFiltersOpen(false)}>
            <div
              className="mobile-filter-drawer"
              onClick={(e) => e.stopPropagation()}
              role="dialog"
              aria-modal="true"
            >
              <div className="mobile-drawer-header">
                <h2>Filters</h2>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={() => setMobileFiltersOpen(false)}
                >
                  ✕
                </button>
              </div>
              <div className="mobile-drawer-body">{renderFilterSidebar()}</div>
              <div className="mobile-drawer-footer">
                <button
                  type="button"
                  className="btn btn-primary btn-block"
                  onClick={() => setMobileFiltersOpen(false)}
                >
                  View {totalCount} Products
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Right Content Area: Results, Active Filters, Sorting, Grid */}
        <main className="storefront-main-content">
          {/* Active Filter Chips */}
          {activeFilters.length > 0 && (
            <div className="active-filters-bar" aria-label="Active Filters">
              <span className="active-filters-label">Active Filters:</span>
              <div className="active-filter-chips-list">
                {activeFilters.map((f) => (
                  <span key={f.key} className="filter-chip">
                    {f.label}
                    <button
                      type="button"
                      className="filter-chip-remove"
                      onClick={f.onRemove}
                      aria-label={`Remove filter ${f.label}`}
                    >
                      ×
                    </button>
                  </span>
                ))}
                <button
                  type="button"
                  className="filter-clear-chip-btn"
                  onClick={clearAllFilters}
                >
                  Clear all
                </button>
              </div>
            </div>
          )}

          {/* Results Toolbar */}
          <div className="catalog-results-toolbar">
            <div className="results-count-box">
              {loading ? (
                <span className="results-count-text">Searching catalog...</span>
              ) : totalCount === 0 ? (
                <span className="results-count-text">0 products</span>
              ) : (
                <span className="results-count-text">
                  Showing <strong>{(pageParam - 1) * 12 + 1}–{Math.min(pageParam * 12, totalCount)}</strong> of{' '}
                  <strong>{totalCount}</strong> products
                </span>
              )}
            </div>

            <div className="results-controls-box">
              {/* Mobile Filter Trigger */}
              <button
                type="button"
                className="btn btn-outline btn-sm mobile-filter-trigger-btn"
                onClick={() => setMobileFiltersOpen(true)}
              >
                Filters {activeFilters.length > 0 && `(${activeFilters.length})`}
              </button>

              {/* Sort Dropdown */}
              <div className="sort-dropdown-box">
                <label htmlFor="catalog-sort-select" className="sort-label">
                  Sort by:
                </label>
                <select
                  id="catalog-sort-select"
                  className="form-input form-input-sm sort-select"
                  value={sortParam}
                  onChange={(e) => updateFilters({ sort: e.target.value })}
                >
                  <option value="newest">Newest Arrivals</option>
                  <option value="price_asc">Price: Low to High</option>
                  <option value="price_desc">Price: High to Low</option>
                  <option value="name_asc">Name: A to Z</option>
                  <option value="name_desc">Name: Z to A</option>
                  <option value="oldest">Oldest</option>
                  {searchParam && <option value="relevance">Relevance</option>}
                </select>
              </div>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="alert alert-danger" role="alert">
              <span>{error}</span>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={fetchProducts}
                style={{ marginLeft: 'auto' }}
              >
                Retry
              </button>
            </div>
          )}

          {/* Product Grid / Loading / Empty State */}
          {loading ? (
            <div className="catalog-loading-grid" aria-live="polite" aria-busy="true">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="card product-card-skeleton">
                  <div className="skeleton-img"></div>
                  <div className="skeleton-text"></div>
                  <div className="skeleton-text short"></div>
                </div>
              ))}
            </div>
          ) : products.length === 0 ? (
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
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <h3 className="empty-title">No products found</h3>
              <p className="empty-desc">
                We could not find any products matching your selected criteria. Try adjusting your filters.
              </p>
              <button type="button" onClick={clearAllFilters} className="btn btn-primary btn-sm">
                Clear All Filters
              </button>
            </div>
          ) : (
            <div className="product-grid">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}

          {/* Pagination Controls */}
          {totalPages > 1 && !loading && (
            <nav className="catalog-pagination-nav" aria-label="Product Pages">
              <button
                type="button"
                className="btn btn-outline btn-sm"
                disabled={pageParam <= 1}
                onClick={() => updateFilters({ page: Math.max(1, pageParam - 1) }, false)}
              >
                ← Previous
              </button>

              <div className="pagination-numbers">
                {[...Array(totalPages)].map((_, idx) => {
                  const pNum = idx + 1;
                  // Render pagination window around current page
                  if (
                    pNum === 1 ||
                    pNum === totalPages ||
                    (pNum >= pageParam - 1 && pNum <= pageParam + 1)
                  ) {
                    return (
                      <button
                        key={pNum}
                        type="button"
                        className={`pagination-num-btn ${pNum === pageParam ? 'active' : ''}`}
                        onClick={() => updateFilters({ page: pNum }, false)}
                      >
                        {pNum}
                      </button>
                    );
                  }
                  if (pNum === pageParam - 2 || pNum === pageParam + 2) {
                    return (
                      <span key={pNum} className="pagination-ellipsis">
                        …
                      </span>
                    );
                  }
                  return null;
                })}
              </div>

              <button
                type="button"
                className="btn btn-outline btn-sm"
                disabled={pageParam >= totalPages}
                onClick={() => updateFilters({ page: Math.min(totalPages, pageParam + 1) }, false)}
              >
                Next →
              </button>
            </nav>
          )}
        </main>
      </div>
    </div>
  );
};

export default ProductsPage;
