import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import productService from '../services/productService';
import productSpecificationService from '../services/productSpecificationService';
import inventoryService from '../../inventory/services/inventoryService';
import AvailabilityBadge from '../../inventory/components/AvailabilityBadge';
import { useAuth } from '../../../context/AuthContext';
import { useCart } from '../../../context/CartContext';
import { WishlistButton } from '../../wishlist';
import { ProductReviewsSection } from '../../reviews';

export const ProductDetailPage = () => {

  const { slug } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { addToCart, actionLoading } = useCart();

  const [product, setProduct] = useState(null);
  const [specs, setSpecs] = useState(null);
  const [availability, setAvailability] = useState(null);
  const [loading, setLoading] = useState(true);
  const [specsLoading, setSpecsLoading] = useState(false);
  const [error, setError] = useState('');
  const [imgError, setImgError] = useState(false);

  // Add to Cart state
  const [quantity, setQuantity] = useState(1);
  const [cartSuccess, setCartSuccess] = useState(false);
  const [cartError, setCartError] = useState('');

  useEffect(() => {
    const fetchProduct = async () => {
      setLoading(true);
      setError('');
      try {
        const prodData = await productService.getProduct(slug);
        setProduct(prodData);

        if (prodData?.id) {
          // Fetch availability status
          try {
            const availData = await inventoryService.getProductAvailability(prodData.id);
            setAvailability(availData);
          } catch {
            // Non-blocking fallback
          }

          // Fetch technical specifications
          setSpecsLoading(true);
          try {
            const specRes = await productSpecificationService.getSpecifications(prodData.id);
            if (specRes && specRes.data) {
              setSpecs(specRes);
            }
          } catch {
            // Specifications are optional/in-progress
          } finally {
            setSpecsLoading(false);
          }
        }
      } catch (err) {
        if (err.response?.status === 404) {
          setError('Product not found. It may have been retired or is currently unavailable.');
        } else {
          setError(
            err.response?.data?.detail || 'Unable to load product details. Please try again.'
          );
        }
      } finally {
        setLoading(false);
      }
    };

    if (slug) {
      fetchProduct();
    }
  }, [slug]);

  const handleAddToCart = async () => {
    setCartSuccess(false);
    setCartError('');

    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    if (user?.role === 'ADMIN') {
      setCartError('Admin accounts manage platform operations and cannot purchase products as a customer.');
      return;
    }

    const result = await addToCart(product.id, quantity);
    if (result.success) {
      setCartSuccess(true);
    } else {
      setCartError(result.error || 'Failed to add item to cart.');
    }
  };

  if (loading) {
    return (
      <div className="container page-wrapper">
        <div className="spinner-wrapper" role="status" aria-live="polite">
          <div className="spinner" aria-hidden="true"></div>
          <p>Loading product details...</p>
        </div>
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="container page-wrapper">
        <div className="card empty-table-box" style={{ maxWidth: '600px', margin: 'var(--space-10) auto' }}>
          <h2 className="empty-table-title">Product Unavailable</h2>
          <p>{error || 'The requested product could not be loaded.'}</p>
          <Link to="/products" className="btn btn-primary" style={{ marginTop: 'var(--space-4)' }}>
            ← Back to Product Catalog
          </Link>
        </div>
      </div>
    );
  }

  const formattedPrice = Number(product.price).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
  });

  const isOutOfStock = availability && (!availability.is_available || availability.availability === 'OUT_OF_STOCK');

  const renderSpecificationRows = () => {
    if (specsLoading) {
      return <p style={{ color: 'var(--color-text-secondary)' }}>Loading technical specifications...</p>;
    }

    if (!specs || !specs.data) {
      return (
        <p className="spec-empty-text">
          Technical specifications are not available yet for this hardware model.
        </p>
      );
    }

    const { type, data } = specs;
    const items = [];

    if (type === 'CPU') {
      if (data.socket) items.push({ label: 'Socket', value: data.socket });
      if (data.core_count) items.push({ label: 'Cores', value: data.core_count });
      if (data.thread_count) items.push({ label: 'Threads', value: data.thread_count });
      if (data.base_clock_ghz) items.push({ label: 'Base Clock', value: `${data.base_clock_ghz} GHz` });
      if (data.boost_clock_ghz) items.push({ label: 'Boost Clock', value: `${data.boost_clock_ghz} GHz` });
      if (data.tdp_watts) items.push({ label: 'TDP', value: `${data.tdp_watts} W` });
      if (data.architecture) items.push({ label: 'Architecture', value: data.architecture });
      if (data.integrated_graphics) items.push({ label: 'Integrated Graphics', value: data.integrated_graphics });
    } else if (type === 'GPU') {
      if (data.chipset) items.push({ label: 'Chipset', value: data.chipset });
      if (data.vram_gb) items.push({ label: 'VRAM', value: `${data.vram_gb} GB` });
      if (data.memory_type) items.push({ label: 'Memory Type', value: data.memory_type });
      if (data.boost_clock_mhz) items.push({ label: 'Boost Clock', value: `${data.boost_clock_mhz} MHz` });
      if (data.core_clock_mhz) items.push({ label: 'Base Clock', value: `${data.core_clock_mhz} MHz` });
      if (data.length_mm) items.push({ label: 'Card Length', value: `${data.length_mm} mm` });
      if (data.tdp_watts) items.push({ label: 'Power Consumption', value: `${data.tdp_watts} W` });
      if (data.recommended_psu_watts) items.push({ label: 'Recommended PSU', value: `${data.recommended_psu_watts} W` });
    } else if (type === 'MOTHERBOARD') {
      if (data.socket) items.push({ label: 'Socket', value: data.socket });
      if (data.chipset) items.push({ label: 'Chipset', value: data.chipset });
      if (data.form_factor) items.push({ label: 'Form Factor', value: data.form_factor });
      if (data.memory_type) items.push({ label: 'Memory Type', value: data.memory_type });
      if (data.memory_slots) items.push({ label: 'Memory Slots', value: data.memory_slots });
      if (data.max_memory_gb) items.push({ label: 'Max Memory', value: `${data.max_memory_gb} GB` });
      if (data.pcie_version) items.push({ label: 'PCIe Standard', value: data.pcie_version });
      items.push({ label: 'Wireless Networking', value: data.wifi ? 'Wi-Fi / Bluetooth Included' : 'No Wi-Fi' });
    } else if (type === 'MEMORY') {
      if (data.memory_type) items.push({ label: 'Memory Type', value: data.memory_type });
      if (data.capacity_gb) items.push({ label: 'Total Capacity', value: `${data.capacity_gb} GB` });
      if (data.speed_mhz) items.push({ label: 'Frequency / Speed', value: `${data.speed_mhz} MHz` });
      if (data.module_count) items.push({ label: 'Module Configuration', value: `${data.module_count} Modules` });
      if (data.cas_latency) items.push({ label: 'CAS Latency', value: `CL${data.cas_latency}` });
    } else if (type === 'STORAGE') {
      if (data.storage_type) items.push({ label: 'Drive Type', value: data.storage_type });
      if (data.capacity_gb) items.push({ label: 'Capacity', value: data.capacity_gb >= 1000 ? `${data.capacity_gb / 1000} TB` : `${data.capacity_gb} GB` });
      if (data.interface) items.push({ label: 'Interface', value: data.interface });
      if (data.form_factor) items.push({ label: 'Form Factor', value: data.form_factor });
      if (data.read_speed_mbps) items.push({ label: 'Sequential Read', value: `${data.read_speed_mbps} MB/s` });
      if (data.write_speed_mbps) items.push({ label: 'Sequential Write', value: `${data.write_speed_mbps} MB/s` });
    } else if (type === 'PSU') {
      if (data.wattage) items.push({ label: 'Total Wattage', value: `${data.wattage} W` });
      if (data.efficiency_rating) items.push({ label: 'Efficiency Rating', value: data.efficiency_rating });
      if (data.modularity) items.push({ label: 'Modularity', value: data.modularity });
      if (data.form_factor) items.push({ label: 'Form Factor', value: data.form_factor });
    } else if (type === 'CASE') {
      if (data.case_type) items.push({ label: 'Case Type', value: data.case_type });
      if (data.supported_motherboard_form_factors) items.push({ label: 'Motherboard Support', value: data.supported_motherboard_form_factors.join(', ') });
      if (data.max_gpu_length_mm) items.push({ label: 'Max GPU Clearance', value: `${data.max_gpu_length_mm} mm` });
      if (data.max_cpu_cooler_height_mm) items.push({ label: 'Max Cooler Height', value: `${data.max_cpu_cooler_height_mm} mm` });
      if (data.psu_form_factor) items.push({ label: 'PSU Clearance Form', value: data.psu_form_factor });
      if (data.drive_bays) items.push({ label: 'Drive Bays', value: data.drive_bays });
    } else if (type === 'COOLING') {
      if (data.cooler_type) items.push({ label: 'Cooler Type', value: data.cooler_type });
      if (data.height_mm) items.push({ label: 'Cooler Height', value: `${data.height_mm} mm` });
      if (data.supported_sockets) items.push({ label: 'Supported Sockets', value: data.supported_sockets.join(', ') });
      if (data.radiator_size_mm) items.push({ label: 'Radiator Size', value: `${data.radiator_size_mm} mm` });
      if (data.fan_size_mm) items.push({ label: 'Fan Size', value: `${data.fan_size_mm} mm` });
      if (data.max_tdp_watts) items.push({ label: 'TDP Rating', value: `${data.max_tdp_watts} W` });
    }

    if (items.length === 0) {
      return (
        <p className="spec-empty-text">
          Technical specifications are not available yet for this hardware model.
        </p>
      );
    }

    return (
      <div className="spec-table-grid">
        {items.map((item, idx) => (
          <div key={idx} className="spec-row">
            <span className="spec-key">{item.label}</span>
            <span className="spec-val">{item.value}</span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="container page-wrapper">
      {/* Breadcrumb Navigation */}
      <div className="product-detail-breadcrumb">
        <Link to="/products" className="back-link">
          ← Back to Catalog
        </Link>
        <span className="breadcrumb-separator">/</span>
        <span className="breadcrumb-current">{product.name}</span>
      </div>

      {/* Main Detail Grid */}
      <div className="product-detail-layout">
        {/* Left Column: Image Showcase */}
        <div className="product-detail-media">
          <div className="product-detail-image-box">
            {product.image_url && !imgError ? (
              <img
                src={product.image_url}
                alt={product.name}
                className="product-detail-image"
                onError={() => setImgError(true)}
              />
            ) : (
              <div className="product-card-placeholder" style={{ minHeight: '340px' }}>
                <svg className="product-placeholder-svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <rect x="4" y="4" width="16" height="16" rx="2" />
                  <rect x="9" y="9" width="6" height="6" />
                  <line x1="9" y1="1" x2="9" y2="4" />
                  <line x1="15" y1="1" x2="15" y2="4" />
                  <line x1="9" y1="20" x2="9" y2="23" />
                  <line x1="15" y1="20" x2="15" y2="23" />
                  <line x1="20" y1="9" x2="23" y2="9" />
                  <line x1="20" y1="15" x2="23" y2="15" />
                  <line x1="1" y1="9" x2="4" y2="9" />
                  <line x1="1" y1="15" x2="4" y2="15" />
                </svg>
                <span className="product-placeholder-text">Hardware Preview</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Information & Summary */}
        <div className="product-detail-info">
          <div className="product-detail-tags">
            <div className="product-detail-meta-text">
              {product.brand?.name && <span className="product-meta-brand">{product.brand.name}</span>}
              {product.brand?.name && product.category?.name && <span className="product-meta-sep"> / </span>}
              {product.category?.name && <span className="product-meta-category">{product.category.name}</span>}
            </div>
            {availability && (
              <AvailabilityBadge status={availability.availability} />
            )}
          </div>

          <h1 className="product-detail-title">{product.name}</h1>

          <div className="product-detail-sku-box">
            <span className="sku-label">SKU:</span>
            <span className="sku-code">{product.sku}</span>
          </div>

          <div className="product-detail-price-box">
            <span className="product-detail-price">{formattedPrice}</span>
          </div>

          {/* Add to Cart Actions Section */}
          <div className="product-detail-cart-action-section">
            {cartSuccess && (
              <div className="alert alert-success" role="alert">
                <span>Added to cart. </span>
                <Link to="/cart" style={{ fontWeight: 600, color: 'inherit', marginLeft: '0.5rem' }}>
                  View Cart →
                </Link>
              </div>
            )}

            {cartError && (
              <div className="alert alert-danger" role="alert">
                <span>{cartError}</span>
              </div>
            )}

            <div className="cart-action-row">
              <div className="quantity-stepper">
                <button
                  type="button"
                  onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                  disabled={quantity <= 1 || isOutOfStock || actionLoading}
                  className="stepper-btn"
                  aria-label="Decrease quantity"
                >
                  −
                </button>
                <span className="stepper-value">{quantity}</span>
                <button
                  type="button"
                  onClick={() => setQuantity((q) => q + 1)}
                  disabled={isOutOfStock || actionLoading}
                  className="stepper-btn"
                  aria-label="Increase quantity"
                >
                  +
                </button>
              </div>

              <button
                type="button"
                onClick={handleAddToCart}
                disabled={isOutOfStock || actionLoading}
                className={`btn btn-primary btn-lg ${isOutOfStock ? 'btn-disabled' : ''}`}
                style={{ flex: 1 }}
              >
                {isOutOfStock
                  ? 'Out of Stock'
                  : actionLoading
                  ? 'Adding...'
                  : 'Add to Cart'}
              </button>

              <WishlistButton
                productId={product.id}
                variant="full"
                className="btn-lg product-detail-wishlist-btn"
              />
            </div>

            <div style={{ marginTop: 'var(--space-3)' }}>
              <Link
                to={`/compatibility?productId=${product.id}`}
                className="btn btn-secondary"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 'var(--space-2)',
                  width: '100%',
                  textDecoration: 'none',
                  fontSize: 'var(--font-size-sm)',
                  fontWeight: 'var(--font-weight-medium)',
                }}
              >
                Check Hardware Compatibility
              </Link>
            </div>
          </div>


          {/* Description Section */}
          <div className="product-detail-description-section">
            <h2 className="detail-section-title">Product Overview</h2>
            <p className="product-detail-description">
              {product.description || 'No detailed overview provided for this component.'}
            </p>
          </div>

          {/* Module 4 Technical Specifications Display */}
          <div className="product-detail-specs-section">
            <h2 className="detail-section-title">Technical Specifications</h2>
            {renderSpecificationRows()}
          </div>

          {/* Module 12 Customer Reviews & Ratings Display */}
          <ProductReviewsSection productId={product.id} productName={product.name} />
        </div>
      </div>
    </div>
  );
};

export default ProductDetailPage;
