import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ProductCard, productService } from '../features/products';
import { categoryService } from '../features/catalog';

export const HomePage = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [categories, setCategories] = useState([]);
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [loadingCategories, setLoadingCategories] = useState(true);
  const [heroSearch, setHeroSearch] = useState('');

  useEffect(() => {
    const fetchHomeData = async () => {
      // 1. Fetch real active categories
      try {
        const catData = await categoryService.listCategories();
        setCategories(Array.isArray(catData) ? catData.slice(0, 8) : []);
      } catch {
        setCategories([]);
      } finally {
        setLoadingCategories(false);
      }

      // 2. Fetch real active products
      try {
        const prodData = await productService.listProducts({ sort: 'newest' });
        const items = Array.isArray(prodData)
          ? prodData
          : prodData?.items || [];
        setFeaturedProducts(items.slice(0, 8));
      } catch {
        setFeaturedProducts([]);
      } finally {
        setLoadingProducts(false);
      }
    };

    fetchHomeData();
  }, []);

  const handleHeroSearch = (e) => {
    e.preventDefault();
    if (heroSearch.trim()) {
      navigate(`/products?search=${encodeURIComponent(heroSearch.trim())}`);
    }
  };

  return (
    <div className="homepage-container">
      {/* 1. Minimalist Hero Section */}
      <section className="home-hero-section">
        <div className="container home-hero-inner">
          <div className="home-hero-content">
            <h1 className="home-hero-headline">
              Precision PC Hardware
            </h1>

            <p className="home-hero-description">
              Curated processors, graphics cards, motherboards, memory, and storage with real-time inventory and verified specifications.
            </p>

            {/* Quick Hero Search Input */}
            <form onSubmit={handleHeroSearch} className="home-hero-search-form" role="search">
              <svg className="hero-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                type="search"
                className="home-hero-search-input"
                placeholder="Search by SKU, brand, or component name..."
                value={heroSearch}
                onChange={(e) => setHeroSearch(e.target.value)}
                aria-label="Search hardware components"
              />
              <button type="submit" className="btn btn-primary home-hero-search-btn">
                Search
              </button>
            </form>

            <div className="home-hero-actions">
              <Link to="/products" className="btn btn-primary">
                Browse Catalog →
              </Link>
              {isAuthenticated ? (
                user?.role === 'ADMIN' ? (
                  <Link to="/admin" className="btn btn-outline">
                    Admin Workspace
                  </Link>
                ) : (
                  <Link to="/orders" className="btn btn-outline">
                    My Orders
                  </Link>
                )
              ) : (
                <Link to="/register" className="btn btn-outline">
                  Create Account
                </Link>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* 2. Popular Categories */}
      <section className="home-categories-section">
        <div className="container">
          <div className="section-header-compact">
            <div>
              <h2 className="section-title">Categories</h2>
            </div>
            <Link to="/products" className="view-all-link">
              All categories →
            </Link>
          </div>

          {loadingCategories ? (
            <div className="categories-grid-skeleton">
              {[1, 2, 3, 4, 5, 6].map((n) => (
                <div key={n} className="category-card-skeleton shimmer" />
              ))}
            </div>
          ) : categories.length > 0 ? (
            <div className="home-categories-grid">
              {categories.map((cat) => (
                <Link
                  key={cat.id}
                  to={`/products?category=${encodeURIComponent(cat.slug || cat.name)}`}
                  className="category-pill-card"
                >
                  <span className="category-pill-name">{cat.name}</span>
                  <span className="category-pill-arrow" aria-hidden="true">→</span>
                </Link>
              ))}
            </div>
          ) : null}
        </div>
      </section>

      {/* 3. Featured Products */}
      <section className="home-products-section">
        <div className="container">
          <div className="section-header-compact">
            <div>
              <h2 className="section-title">Featured Products</h2>
            </div>
            <Link to="/products" className="view-all-link">
              Full catalog →
            </Link>
          </div>

          {loadingProducts ? (
            <div className="products-grid-skeleton">
              {[1, 2, 3, 4].map((n) => (
                <div key={n} className="product-card-skeleton shimmer" />
              ))}
            </div>
          ) : featuredProducts.length > 0 ? (
            <div className="products-grid">
              {featuredProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          ) : (
            <div className="empty-state-box">
              <h3>No products found</h3>
              <p>Hardware products will appear here once registered in the catalog.</p>
              <Link to="/products" className="btn btn-outline btn-sm">
                Browse catalog
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* 4. Trust & Capabilities */}
      <section className="home-trust-section">
        <div className="container">
          <div className="home-trust-grid">
            <div className="trust-item">
              <h3 className="trust-title">Technical Specifications</h3>
              <p className="trust-text">
                Detailed socket compatibility, power draw, clock speeds, and hardware dimensions.
              </p>
            </div>

            <div className="trust-item">
              <h3 className="trust-title">Verified Reviews</h3>
              <p className="trust-text">
                Customer ratings and written reviews verified exclusively from confirmed purchase orders.
              </p>
            </div>

            <div className="trust-item">
              <h3 className="trust-title">Live Inventory</h3>
              <p className="trust-text">
                Accurate warehouse stock levels with atomic reservation at checkout.
              </p>
            </div>

            <div className="trust-item">
              <h3 className="trust-title">Cash on Delivery</h3>
              <p className="trust-text">
                Doorstep cash settlement across supported Philippine delivery locations.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
