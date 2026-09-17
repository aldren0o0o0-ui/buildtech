import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Footer = () => {
  const { isAuthenticated, user } = useAuth();
  const currentYear = new Date().getFullYear();

  return (
    <footer className="app-footer">
      <div className="container footer-container">
        <div className="footer-grid">
          {/* Brand Column */}
          <div className="footer-brand-col">
            <Link to="/" className="footer-brand" aria-label="BuildTech Home">
              Build<span className="brand-dot">Tech</span>
            </Link>
            <p className="footer-tagline">
              High-performance PC hardware and electronics curated for builders, creators, and professionals.
            </p>
            <ul className="footer-trust-list">
              <li>Real-time inventory verification</li>
              <li>Verified purchaser reviews</li>
              <li>Cash on delivery payment</li>
            </ul>
          </div>

          {/* Quick Links */}
          <div className="footer-nav-col">
            <h4 className="footer-heading">Shop Hardware</h4>
            <ul className="footer-links">
              <li>
                <Link to="/products">All Products</Link>
              </li>
              <li>
                <Link to="/products?category=graphics-cards">Graphics Cards</Link>
              </li>
              <li>
                <Link to="/products?category=processors">Processors (CPUs)</Link>
              </li>
              <li>
                <Link to="/products?category=motherboards">Motherboards</Link>
              </li>
              <li>
                <Link to="/products?category=memory">Memory & RAM</Link>
              </li>
              <li>
                <Link to="/products?category=storage">SSD & Storage</Link>
              </li>
            </ul>
          </div>

          {/* Customer Support & Services */}
          <div className="footer-nav-col">
            <h4 className="footer-heading">Customer Account</h4>
            <ul className="footer-links">
              {isAuthenticated ? (
                <>
                  <li>
                    <Link to="/account">My Profile</Link>
                  </li>
                  <li>
                    <Link to="/orders">Order History</Link>
                  </li>
                  <li>
                    <Link to="/wishlist">Saved Wishlist</Link>
                  </li>
                  <li>
                    <Link to="/cart">Shopping Cart</Link>
                  </li>
                  <li>
                    <Link to="/account/addresses">Saved Addresses</Link>
                  </li>
                </>
              ) : (
                <>
                  <li>
                    <Link to="/login">Sign In</Link>
                  </li>
                  <li>
                    <Link to="/register">Create Account</Link>
                  </li>
                  <li>
                    <Link to="/products">Browse Catalog</Link>
                  </li>
                </>
              )}
              {isAuthenticated && user?.role === 'ADMIN' && (
                <li>
                  <Link to="/admin" className="footer-admin-link">
                    Admin Workspace
                  </Link>
                </li>
              )}
            </ul>
          </div>

          {/* Operational Commitments */}
          <div className="footer-nav-col">
            <h4 className="footer-heading">BuildTech Guarantee</h4>
            <p className="footer-guarantee-text">
              Every component sold is backed by manufacturer warranties, authenticated specifications, and verified customer reviews.
            </p>
            <div className="footer-payment-note">
              <span>Payment: <strong>Cash on Delivery (COD)</strong></span>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="footer-bottom">
          <p className="footer-copyright">
            &copy; {currentYear} BuildTech E-Commerce Platform. All rights reserved.
          </p>
          <div className="footer-meta-links">
            <span className="footer-meta-item">Production Baseline Modules 1–13</span>
            <span className="footer-meta-dot">•</span>
            <span className="footer-meta-item">Philippines Delivery</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
