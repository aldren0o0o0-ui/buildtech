import React from 'react';
import { Link } from 'react-router-dom';

export const AdminNav = ({ activeTitle, actions }) => {
  return (
    <div className="admin-page-topbar">
      <div className="admin-page-topbar-inner">
        <div className="admin-breadcrumb">
          <Link to="/admin" className="admin-breadcrumb-root">Admin</Link>
          {activeTitle && (
            <>
              <span className="admin-breadcrumb-separator">/</span>
              <span className="admin-breadcrumb-current">{activeTitle}</span>
            </>
          )}
        </div>
        {actions && <div className="admin-page-topbar-actions">{actions}</div>}
      </div>
    </div>
  );
};

export default AdminNav;

