import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import authService from '../features/auth/services/authService';
import { setAccessToken } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [accessTokenState, setAccessTokenState] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Updates in-memory token both in Axios config and React state
  const handleSetAccessToken = useCallback((token) => {
    setAccessToken(token);
    setAccessTokenState(token);
  }, []);

  /**
   * Refreshes the session on startup or when needed via HttpOnly cookie.
   */
  const refreshSession = useCallback(async () => {
    try {
      const data = await authService.refresh();
      handleSetAccessToken(data.access_token);
      setUser(data.user);
      return data;
    } catch {
      handleSetAccessToken(null);
      setUser(null);
      return null;
    }
  }, [handleSetAccessToken]);

  // Load active session on mount
  useEffect(() => {
    let isMounted = true;
    const initializeAuth = async () => {
      try {
        await refreshSession();
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    initializeAuth();
    return () => {
      isMounted = false;
    };
  }, [refreshSession]);

  /**
   * Log in user
   */
  const login = async (credentials) => {
    const data = await authService.login(credentials);
    handleSetAccessToken(data.access_token);
    setUser(data.user);
    return data.user;
  };

  /**
   * Register new user
   */
  const register = async (userData) => {
    return await authService.register(userData);
  };

  /**
   * Log out user and clear state
   */
  const logout = async () => {
    try {
      await authService.logout();
    } catch {
      // Ignore network failure on logout and clear local state anyway
    } finally {
      handleSetAccessToken(null);
      setUser(null);
    }
  };

  /**
   * Reload current user profile from backend
   */
  const refreshUser = async () => {
    try {
      const userData = await authService.getMe();
      setUser(userData);
      return userData;
    } catch (err) {
      if (err.response?.status === 401) {
        handleSetAccessToken(null);
        setUser(null);
      }
      throw err;
    }
  };

  /**
   * Update profile (first_name, last_name)
   */
  const updateProfile = async (profileData) => {
    const updatedUser = await authService.updateMe(profileData);
    setUser(updatedUser);
    return updatedUser;
  };

  /**
   * Change password
   */
  const changePassword = async (passwordData) => {
    return await authService.changePassword(passwordData);
  };

  const value = {
    user,
    accessToken: accessTokenState,
    isAuthenticated: !!user && !!accessTokenState,
    isLoading,
    login,
    register,
    logout,
    refreshSession,
    refreshUser,
    updateProfile,
    changePassword,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
