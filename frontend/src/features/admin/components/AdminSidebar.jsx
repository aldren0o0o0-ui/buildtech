import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';

export const AdminSidebar = ({ mobileOpen, onCloseMobile }) => {
  const { user } = useAuth();

  const navItems = [
    {
      to: '/admin',
      label: 'Dashboard',
      end: true,
      icon: (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <rect x="3" y="3" width="7" height="7" />
          <rect x="14" y="3" width="7" height="7" />
          <rect x="14" y="14" width="7" height="7" />
          <rect x="3" y="14" width="7" height="7" />
        </svg>
      ),
    },
    {
      to: '/admin/orders',
      label: 'Orders',
      icon: (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
          <line x1="3" y1="6" x2="21" y2="6" />
          <path d="M16 10a4 4 0 0 1-8 0" />
        </svg>
      ),
    },
    {
      to: '/admin/inventory',
      label: 'Inventory',
      icon: (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polygon points="12 2 2 7 12 12 22 7 12 2" />
          <polyline points="2 17 12 22 22 17" />
          <polyline points="2 12 12 17 22 12" />
        </svg>
      ),
    },
    {
      to: '/admin/products',
      label: 'Products',
      icon: (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <rect x="4" y="4" width="16" height="16" rx="2" />
          <rect x="9" y="9" width="6" height="6" />
          <line x1="9" y1="1" x2="9" y2="4" />
          <line x1="15" y1="1" x2="15" y2="4" />
          <line x1="9" y1="20" x2="9" y2="23" />
          <line x1="15" y1="20" x2="15" y2="23" />
          <line x1="20" y1="9" x2="23" y2="9" />
          <line x1="20" y1="14" x2="23" y2="14" />
          <line x1="1" y1="9" x2="4" y2="9" />
          <line x1="1" y1="14" x2="4" y2="14" />
        </svg>
      ),
    },
    {
      to: '/admin/categories',
      label: 'Categories',
      icon: (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
        </svg>
      ),
    },
    {
      to: '/admin/brands',
      label: 'Brands',
      icon: (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" />
          <line x1="7" y1="7" x2="7.01" y2="7" />
        </svg>
      ),
    },
    {
      to: '/admin/reviews',
      label: 'Reviews',
      icon: (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
        </svg>
      ),
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="admin-sidebar-backdrop"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      <aside
        className={`admin-sidebar ${mobileOpen ? 'admin-sidebar-open' : ''}`}
        aria-label="Admin Navigation Sidebar"
      >
        <div className="admin-sidebar-top">
          <div className="admin-sidebar-header">
            <div className="admin-sidebar-brand">
              <span className="admin-badge">Admin Portal</span>
              <span className="admin-brand-title">BuildTech Management</span>
            </div>
            {onCloseMobile && (
              <button
                type="button"
                className="admin-sidebar-close-btn"
                onClick={onCloseMobile}
                aria-label="Close navigation sidebar"
              >
                ✕
              </button>
            )}
          </div>

          <nav className="admin-sidebar-nav">
            <div className="admin-nav-group-label">Operations</div>
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  `admin-sidebar-link ${isActive ? 'active' : ''}`
                }
              >
                <span className="admin-sidebar-icon">{item.icon}</span>
                <span className="admin-sidebar-label">{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="admin-sidebar-bottom">
          <Link
            to="/"
            className="admin-sidebar-storefront-link"
            title="Return to customer-facing catalog"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
            <span>Customer Storefront</span>
          </Link>

          <div className="admin-user-profile-widget">
            <div className="admin-user-avatar">
              {user?.first_name ? user.first_name[0].toUpperCase() : 'A'}
            </div>
            <div className="admin-user-details">
              <span className="admin-user-name">
                {user?.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : 'Administrator'}
              </span>
              <span className="admin-user-email" title={user?.email}>
                {user?.email || 'admin@buildtech.com'}
              </span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};

export default AdminSidebar;
