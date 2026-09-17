import api from '../../../services/api';

export const authService = {
  /**
   * Register a new user account.
   */
  register: async (userData) => {
    const response = await api.post('/api/v1/auth/register', userData);
    return response.data;
  },

  /**
   * Log in user with credentials.
   * Backend returns access token in body and sets HttpOnly refresh cookie.
   */
  login: async (credentials) => {
    const response = await api.post('/api/v1/auth/login', credentials);
    return response.data;
  },

  /**
   * Refresh session using HttpOnly cookie.
   */
  refresh: async () => {
    const response = await api.post('/api/v1/auth/refresh');
    return response.data;
  },

  /**
   * Log out current session and clear HttpOnly cookie.
   */
  logout: async () => {
    const response = await api.post('/api/v1/auth/logout');
    return response.data;
  },

  /**
   * Get current authenticated user profile.
   */
  getMe: async () => {
    const response = await api.get('/api/v1/users/me');
    return response.data;
  },

  /**
   * Update first_name and last_name of current user.
   */
  updateMe: async (profileData) => {
    const response = await api.patch('/api/v1/users/me', profileData);
    return response.data;
  },

  /**
   * Change current user's password.
   */
  changePassword: async (passwordData) => {
    const response = await api.post('/api/v1/users/me/change-password', passwordData);
    return response.data;
  },
};

export default authService;
