import React from 'react';
import { Link } from 'react-router-dom';

export const UnauthorizedPage = () => {
  return (
    <div className="auth-page-wrapper">
      <div className="auth-card unauthorized-content">
        <div className="status-code-badge" aria-hidden="true">
          403
        </div>
        <h1 className="auth-title">Access Denied</h1>
        <p className="auth-subtitle" style={{ marginBottom: '1.5rem' }}>
          You do not have permission to access the requested administrator area.
        </p>

        <div className="form-actions form-actions-center">
          <Link to="/" className="btn btn-outline">
            Return Home
          </Link>
          <Link to="/account" className="btn btn-primary">
            Go to Account
          </Link>
        </div>
      </div>
    </div>
  );
};

export default UnauthorizedPage;
