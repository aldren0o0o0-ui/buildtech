import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import AdminSidebar from '../features/admin/components/AdminSidebar';

export const AdminLayout = () => {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="admin-layout">
      {/* Mobile Top Sub-Header */}
      <div className="admin-mobile-bar">
        <button
          type="button"
          className="admin-mobile-toggle-btn"
          onClick={() => setMobileSidebarOpen(true)}
          aria-label="Open Admin Menu"
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
          <span>Admin Menu</span>
        </button>
        <span className="admin-mobile-badge">Back-Office</span>
      </div>

      <div className="admin-body">
        <AdminSidebar
          mobileOpen={mobileSidebarOpen}
          onCloseMobile={() => setMobileSidebarOpen(false)}
        />
        <div className="admin-main-viewport">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default AdminLayout;
