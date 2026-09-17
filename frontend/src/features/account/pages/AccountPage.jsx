import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../../context/AuthContext';


export const AccountPage = () => {
  const { user, updateProfile, changePassword } = useAuth();

  // Profile Form State
  const [profileData, setProfileData] = useState({
    firstName: '',
    lastName: '',
  });
  const [profileSuccess, setProfileSuccess] = useState('');
  const [profileError, setProfileError] = useState('');
  const [profileSubmitting, setProfileSubmitting] = useState(false);

  // Password Form State
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [passwordSubmitting, setPasswordSubmitting] = useState(false);

  useEffect(() => {
    if (user) {
      setProfileData({
        firstName: user.first_name || '',
        lastName: user.last_name || '',
      });
    }
  }, [user]);

  // Profile update handler
  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData((prev) => ({ ...prev, [name]: value }));
    if (profileError) setProfileError('');
    if (profileSuccess) setProfileSuccess('');
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileError('');
    setProfileSuccess('');

    const trimmedFirst = profileData.firstName.trim();
    const trimmedLast = profileData.lastName.trim();

    if (!trimmedFirst || !trimmedLast) {
      setProfileError('Both first name and last name are required.');
      return;
    }

    setProfileSubmitting(true);
    try {
      await updateProfile({
        first_name: trimmedFirst,
        last_name: trimmedLast,
      });
      setProfileSuccess('Profile updated successfully.');
    } catch (err) {
      const detail = err.response?.data?.detail;
      setProfileError(
        typeof detail === 'string'
          ? detail
          : 'Failed to update profile. Please try again.'
      );
    } finally {
      setProfileSubmitting(false);
    }
  };

  // Password change handler
  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData((prev) => ({ ...prev, [name]: value }));
    if (passwordError) setPasswordError('');
    if (passwordSuccess) setPasswordSuccess('');
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    if (!passwordData.currentPassword) {
      setPasswordError('Please enter your current password.');
      return;
    }

    if (!passwordData.newPassword) {
      setPasswordError('Please enter a new password.');
      return;
    }

    if (passwordData.newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters long.');
      return;
    }

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError('New passwords do not match.');
      return;
    }

    setPasswordSubmitting(true);
    try {
      await changePassword({
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword,
      });
      setPasswordSuccess('Password updated successfully.');
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
    } catch (err) {
      const detail = err.response?.data?.detail;
      setPasswordError(
        typeof detail === 'string'
          ? detail
          : 'Failed to change password. Please check your current password and try again.'
      );
    } finally {
      setPasswordSubmitting(false);
    }
  };

  const formattedDate = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : '—';

  return (
    <div className="container page-wrapper">
      <div className="account-container">
        {/* Account Header */}
        <div className="account-header-block">
          <div>
            <h1 className="account-title">Account Settings</h1>
            <p className="account-email-sub">{user?.email}</p>
          </div>
          <div className="account-meta-pills">
            <span
              className={`badge ${
                user?.role === 'ADMIN' ? 'badge-admin' : 'badge-customer'
              }`}
            >
              {user?.role}
            </span>
            <span className="badge badge-subtle">
              Member since {formattedDate}
            </span>
          </div>
        </div>

        {/* Section 1: Profile Information */}
        <div className="account-card-section">
          <h2 className="section-title">Personal Details</h2>
          <p className="section-desc">
            Update your public display name and customer profile.
          </p>

          {profileSuccess && (
            <div className="alert alert-success" role="alert" aria-live="polite">
              <span>{profileSuccess}</span>
            </div>
          )}

          {profileError && (
            <div className="alert alert-danger" role="alert" aria-live="polite">
              <span>{profileError}</span>
            </div>
          )}

          <form onSubmit={handleProfileSubmit} noValidate>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="acc-firstName" className="form-label">
                  First Name
                </label>
                <input
                  id="acc-firstName"
                  type="text"
                  name="firstName"
                  className="form-input"
                  value={profileData.firstName}
                  onChange={handleProfileChange}
                  required
                  disabled={profileSubmitting}
                />
              </div>

              <div className="form-group">
                <label htmlFor="acc-lastName" className="form-label">
                  Last Name
                </label>
                <input
                  id="acc-lastName"
                  type="text"
                  name="lastName"
                  className="form-input"
                  value={profileData.lastName}
                  onChange={handleProfileChange}
                  required
                  disabled={profileSubmitting}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="acc-email" className="form-label">
                Email Address
              </label>
              <input
                id="acc-email"
                type="email"
                className="form-input"
                value={user?.email || ''}
                disabled
                style={{
                  backgroundColor: 'var(--color-surface-muted)',
                  cursor: 'not-allowed',
                  color: 'var(--color-text-secondary)',
                }}
              />
              <span className="form-helper">
                Account email cannot be modified directly for security reasons.
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--space-2)' }}>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={profileSubmitting}
              >
                {profileSubmitting ? 'Saving...' : 'Save Profile'}
              </button>
            </div>
          </form>
        </div>

        {/* Section 2: Security & Password */}
        <div className="account-card-section">
          <h2 className="section-title">Change Password</h2>
          <p className="section-desc">
            Ensure your account is using a long, random password to stay secure.
          </p>

          {passwordSuccess && (
            <div className="alert alert-success" role="alert" aria-live="polite">
              <span>{passwordSuccess}</span>
            </div>
          )}

          {passwordError && (
            <div className="alert alert-danger" role="alert" aria-live="polite">
              <span>{passwordError}</span>
            </div>
          )}

          <form onSubmit={handlePasswordSubmit} noValidate>
            <div className="form-group">
              <label htmlFor="acc-currentPassword" className="form-label">
                Current Password
              </label>
              <input
                id="acc-currentPassword"
                type="password"
                name="currentPassword"
                className="form-input"
                placeholder="••••••••"
                value={passwordData.currentPassword}
                onChange={handlePasswordChange}
                autoComplete="current-password"
                required
                disabled={passwordSubmitting}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="acc-newPassword" className="form-label">
                  New Password
                </label>
                <input
                  id="acc-newPassword"
                  type="password"
                  name="newPassword"
                  className="form-input"
                  placeholder="Min. 8 characters"
                  value={passwordData.newPassword}
                  onChange={handlePasswordChange}
                  autoComplete="new-password"
                  required
                  disabled={passwordSubmitting}
                />
              </div>

              <div className="form-group">
                <label htmlFor="acc-confirmPassword" className="form-label">
                  Confirm New Password
                </label>
                <input
                  id="acc-confirmPassword"
                  type="password"
                  name="confirmPassword"
                  className="form-input"
                  placeholder="Re-enter new password"
                  value={passwordData.confirmPassword}
                  onChange={handlePasswordChange}
                  autoComplete="new-password"
                  required
                  disabled={passwordSubmitting}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 'var(--space-2)' }}>
              <button
                type="submit"
                className="btn btn-outline"
                disabled={passwordSubmitting}
              >
                {passwordSubmitting ? 'Updating...' : 'Update Password'}
              </button>
            </div>
          </form>
        </div>

        {/* Section 3: Shipping Addresses (Module 9) */}
        {user?.role === 'CUSTOMER' && (
          <div className="account-card-section">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h2 className="section-title">Shipping Addresses</h2>
                <p className="section-desc">
                  Manage your saved delivery addresses and default shipping options.
                </p>
              </div>
              <Link to="/account/addresses" className="btn btn-primary btn-sm">
                Manage Addresses →
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};


export default AccountPage;
