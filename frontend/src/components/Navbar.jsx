import React, { useState, useEffect, useRef } from 'react';
import { Link, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';
import { useWishlist } from '../context/WishlistContext';
import ThemeToggle from './ThemeToggle';

export const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const { cartCount } = useCart();
  const { wishlistCount } = useWishlist();
  const navigate = useNavigate();
  const location = useLocation();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const mobileMenuRef = useRef(null);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // Handle ESC key to close mobile menu
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && mobileMenuOpen) {
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mobileMenuOpen]);

  // Prevent background scroll when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileMenuOpen]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery('');
      setMobileMenuOpen(false);
    }
  };

  const isCustomer = isAuthenticated && user?.role === 'CUSTOMER';
  const isAdmin = isAuthenticated && user?.role === 'ADMIN';

  return (
    <header className="navbar">
      <div className="container navbar-inner">
        {/* Left Section: Brand & Primary Links */}
        <div className="navbar-left">
          <Link to="/" className="navbar-brand" aria-label="BuildTech Home">
            Build<span className="brand-dot">Tech</span>
          </Link>

          <nav className="navbar-nav desktop-only" aria-label="Primary Navigation">
            <NavLink
              to="/"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
              end
            >
              Home
            </NavLink>

            <NavLink
              to="/products"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              Products
            </NavLink>

            <NavLink
              to="/compatibility"
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              Compatibility
            </NavLink>

            {isCustomer && (
              <NavLink
                to="/orders"
                className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
              >
                Orders
              </NavLink>
            )}

            {isAdmin && (
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  isActive ? 'nav-link admin-nav-pill active' : 'nav-link admin-nav-pill'
                }
              >
                Admin
              </NavLink>
            )}
          </nav>
        </div>

        {/* Center: Global Search Bar (Desktop) */}
        <div className="navbar-search desktop-only">
          <form onSubmit={handleSearchSubmit} className="navbar-search-form" role="search">
            <svg className="navbar-search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="search"
              className="navbar-search-input"
              placeholder="Search graphics cards, CPUs, memory..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search hardware catalog"
            />
            {searchQuery && (
              <button
                type="button"
                className="navbar-search-clear"
                onClick={() => setSearchQuery('')}
                aria-label="Clear search input"
              >
                ✕
              </button>
            )}
          </form>
        </div>

        {/* Right Section: Actions, Counters, Auth & Theme */}
        <div className="navbar-right">
          {/* Wishlist Link (Desktop) */}
          {isCustomer && (
            <NavLink
              to="/wishlist"
              className={({ isActive }) =>
                isActive ? 'nav-action-btn active desktop-only' : 'nav-action-btn desktop-only'
              }
              aria-label={`Wishlist (${wishlistCount} items)`}
              title="Saved Wishlist"
            >
              <svg className="nav-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
              </svg>
              {wishlistCount > 0 && (
                <span className="nav-badge" aria-hidden="true">
                  {wishlistCount}
                </span>
              )}
            </NavLink>
          )}

          {/* Cart Link (Desktop & Mobile) */}
          {isCustomer && (
            <NavLink
              to="/cart"
              className={({ isActive }) =>
                isActive ? 'nav-action-btn nav-cart-btn active' : 'nav-action-btn nav-cart-btn'
              }
              aria-label={`Shopping cart (${cartCount} items)`}
              title="Shopping Cart"
            >
              <svg className="nav-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <circle cx="9" cy="21" r="1" />
                <circle cx="20" cy="21" r="1" />
                <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
              </svg>
              {cartCount > 0 && (
                <span className="nav-badge" aria-hidden="true">
                  {cartCount}
                </span>
              )}
            </NavLink>
          )}

          {/* Theme Switcher Toggle */}
          <ThemeToggle />

          {/* Desktop User Authentication Controls */}
          <div className="desktop-only">
            {isAuthenticated ? (
              <div className="user-nav-group">
                <Link to="/account" className="user-greeting-link" title="Manage Account">
                  <span className="user-avatar-pill">
                    {user?.first_name ? user.first_name[0].toUpperCase() : 'U'}
                  </span>
                  <span className="user-greeting-name">{user?.first_name}</span>
                </Link>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="btn btn-ghost btn-sm"
                  aria-label="Sign out of account"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="auth-nav-buttons">
                <Link to="/login" className="btn btn-ghost btn-sm">
                  Sign In
                </Link>
                <Link to="/register" className="btn btn-primary btn-sm">
                  Register
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Hamburger Menu Toggle */}
          <button
            type="button"
            className="mobile-menu-toggle mobile-only"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
            aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-nav-drawer"
          >
            <span className="hamburger-icon" aria-hidden="true">
              {mobileMenuOpen ? '✕' : '☰'}
            </span>
          </button>
        </div>
      </div>

      {/* Mobile Slide-Out Drawer & Overlay */}
      {mobileMenuOpen && (
        <div
          className="mobile-nav-overlay mobile-only"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      <div
        id="mobile-nav-drawer"
        ref={mobileMenuRef}
        className={`mobile-nav-drawer mobile-only ${mobileMenuOpen ? 'open' : ''}`}
        aria-hidden={!mobileMenuOpen}
      >
        <div className="mobile-nav-header">
          <Link to="/" className="navbar-brand" onClick={() => setMobileMenuOpen(false)}>
            Build<span className="brand-dot">Tech</span>
          </Link>
          <button
            type="button"
            className="btn btn-ghost btn-sm mobile-nav-close"
            onClick={() => setMobileMenuOpen(false)}
            aria-label="Close menu"
          >
            ✕
          </button>
        </div>

        {/* Mobile Search Input */}
        <div className="mobile-nav-search">
          <form onSubmit={handleSearchSubmit} className="navbar-search-form" role="search">
            <svg className="navbar-search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="search"
              className="navbar-search-input"
              placeholder="Search components..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search catalog"
            />
            <button type="submit" className="btn btn-primary btn-sm">
              Search
            </button>
          </form>
        </div>

        {/* Mobile Navigation Links */}
        <nav className="mobile-nav-links" aria-label="Mobile Navigation">
          <NavLink
            to="/"
            className={({ isActive }) => (isActive ? 'mobile-nav-link active' : 'mobile-nav-link')}
            end
          >
            Home
          </NavLink>
          <NavLink
            to="/products"
            className={({ isActive }) => (isActive ? 'mobile-nav-link active' : 'mobile-nav-link')}
          >
            Products
          </NavLink>

          <NavLink
            to="/compatibility"
            className={({ isActive }) => (isActive ? 'mobile-nav-link active' : 'mobile-nav-link')}
          >
            Compatibility
          </NavLink>

          {isCustomer && (
            <>
              <NavLink
                to="/cart"
                className={({ isActive }) =>
                  isActive ? 'mobile-nav-link active' : 'mobile-nav-link'
                }
              >
                Cart {cartCount > 0 && `(${cartCount})`}
              </NavLink>
              <NavLink
                to="/wishlist"
                className={({ isActive }) =>
                  isActive ? 'mobile-nav-link active' : 'mobile-nav-link'
                }
              >
                Wishlist {wishlistCount > 0 && `(${wishlistCount})`}
              </NavLink>
              <NavLink
                to="/orders"
                className={({ isActive }) =>
                  isActive ? 'mobile-nav-link active' : 'mobile-nav-link'
                }
              >
                Orders
              </NavLink>
              <NavLink
                to="/account/addresses"
                className={({ isActive }) =>
                  isActive ? 'mobile-nav-link active' : 'mobile-nav-link'
                }
              >
                Addresses
              </NavLink>
            </>
          )}

          {isAuthenticated && (
            <NavLink
              to="/account"
              className={({ isActive }) =>
                isActive ? 'mobile-nav-link active' : 'mobile-nav-link'
              }
            >
              Account
            </NavLink>
          )}

          {isAdmin && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                isActive ? 'mobile-nav-link admin-link active' : 'mobile-nav-link admin-link'
              }
            >
              Admin Workspace
            </NavLink>
          )}
        </nav>

        {/* Mobile Footer with Auth Actions */}
        <div className="mobile-nav-footer">
          {isAuthenticated ? (
            <div className="mobile-user-profile">
              <div className="mobile-user-info">
                <span className="mobile-user-name">
                  {user?.first_name} {user?.last_name}
                </span>
                <span className="mobile-user-email">{user?.email}</span>
                <span className={`badge ${isAdmin ? 'badge-admin' : 'badge-customer'}`}>
                  {user?.role}
                </span>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="btn btn-outline btn-block"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <div className="mobile-auth-actions">
              <Link to="/login" className="btn btn-outline btn-block">
                Sign In
              </Link>
              <Link to="/register" className="btn btn-primary btn-block">
                Create Account
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
