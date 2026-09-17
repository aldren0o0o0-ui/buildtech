import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useAuth } from './AuthContext';
import cartService from '../features/cart/services/cartService';

const CartContext = createContext(null);

export const CartProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  const isCustomer = isAuthenticated && user?.role === 'CUSTOMER';

  /**
   * Fetches the current customer cart.
   */
  const refreshCart = useCallback(async () => {
    if (!isCustomer) {
      setCart(null);
      return null;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await cartService.getCart();
      setCart(data);
      return data;
    } catch (err) {
      // 403 occurs if user is Admin, 401 if unauthenticated
      if (err.response?.status !== 403 && err.response?.status !== 401) {
        setError(err.response?.data?.detail || 'Failed to load shopping cart.');
      }
      setCart(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, [isCustomer]);

  // Load cart when user logs in or switches
  useEffect(() => {
    if (isCustomer) {
      refreshCart();
    } else {
      setCart(null);
    }
  }, [isCustomer, refreshCart]);

  /**
   * Adds an item to the customer's cart.
   */
  const addToCart = async (productId, quantity = 1) => {
    setActionLoading(true);
    setError(null);
    try {
      const updatedCart = await cartService.addToCart(productId, quantity);
      setCart(updatedCart);
      return { success: true, cart: updatedCart };
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to add product to cart.';
      setError(message);
      return { success: false, error: message };
    } finally {
      setActionLoading(false);
    }
  };

  /**
   * Updates an item's quantity in the cart.
   */
  const updateQuantity = async (itemId, quantity) => {
    setActionLoading(true);
    setError(null);
    try {
      const updatedCart = await cartService.updateCartItem(itemId, quantity);
      setCart(updatedCart);
      return { success: true, cart: updatedCart };
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to update item quantity.';
      setError(message);
      return { success: false, error: message };
    } finally {
      setActionLoading(false);
    }
  };

  /**
   * Removes an item from the cart.
   */
  const removeItem = async (itemId) => {
    setActionLoading(true);
    setError(null);
    try {
      const updatedCart = await cartService.removeCartItem(itemId);
      setCart(updatedCart);
      return { success: true, cart: updatedCart };
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to remove item from cart.';
      setError(message);
      return { success: false, error: message };
    } finally {
      setActionLoading(false);
    }
  };

  /**
   * Clears the entire cart.
   */
  const clearCart = async () => {
    setActionLoading(true);
    setError(null);
    try {
      const emptyCart = await cartService.clearCart();
      setCart(emptyCart);
      return { success: true, cart: emptyCart };
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to clear cart.';
      setError(message);
      return { success: false, error: message };
    } finally {
      setActionLoading(false);
    }
  };

  const cartCount = cart ? cart.total_quantity : 0;

  const value = {
    cart,
    cartCount,
    loading,
    actionLoading,
    error,
    refreshCart,
    addToCart,
    updateQuantity,
    removeItem,
    clearCart,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

export default CartContext;
