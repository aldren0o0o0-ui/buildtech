import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useMemo,
} from 'react';
import { useAuth } from './AuthContext';
import wishlistService from '../features/wishlist/services/wishlistService';

const WishlistContext = createContext(null);

export const WishlistProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [wishlist, setWishlist] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  const isCustomer = isAuthenticated && user?.role === 'CUSTOMER';

  /**
   * Refreshes the customer's wishlist from the server.
   */
  const refreshWishlist = useCallback(async () => {
    if (!isCustomer) {
      setWishlist(null);
      return null;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await wishlistService.getWishlist();
      setWishlist(data);
      return data;
    } catch (err) {
      if (err.response?.status !== 403 && err.response?.status !== 401) {
        setError(err.response?.data?.detail || 'Failed to load wishlist.');
      }
      setWishlist(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, [isCustomer]);

  // Load wishlist on customer login or switch
  useEffect(() => {
    if (isCustomer) {
      refreshWishlist();
    } else {
      setWishlist(null);
    }
  }, [isCustomer, refreshWishlist]);

  /**
   * Fast O(1) in-memory lookup map of wishlisted product IDs to item IDs.
   * Completely eliminates N+1 network requests across catalog product cards.
   */
  const wishlistedProductMap = useMemo(() => {
    const map = new Map();
    if (wishlist?.items) {
      wishlist.items.forEach((item) => {
        if (item.product?.id) {
          map.set(item.product.id, item.id);
        }
      });
    }
    return map;
  }, [wishlist]);

  const isWishlisted = useCallback(
    (productId) => {
      if (!productId) return false;
      return wishlistedProductMap.has(Number(productId));
    },
    [wishlistedProductMap]
  );

  const getWishlistItemId = useCallback(
    (productId) => {
      if (!productId) return null;
      return wishlistedProductMap.get(Number(productId)) || null;
    },
    [wishlistedProductMap]
  );

  /**
   * Adds a product to the wishlist.
   */
  const addToWishlist = async (productId) => {
    setActionLoading(true);
    setError(null);
    try {
      const updatedWishlist = await wishlistService.addToWishlist(productId);
      setWishlist(updatedWishlist);
      return { success: true, wishlist: updatedWishlist };
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to add product to wishlist.';
      setError(message);
      return { success: false, error: message };
    } finally {
      setActionLoading(false);
    }
  };

  /**
   * Removes an item from the wishlist by item ID.
   */
  const removeFromWishlist = async (itemId) => {
    setActionLoading(true);
    setError(null);
    try {
      const updatedWishlist = await wishlistService.removeFromWishlist(itemId);
      setWishlist(updatedWishlist);
      return { success: true, wishlist: updatedWishlist };
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to remove product from wishlist.';
      setError(message);
      return { success: false, error: message };
    } finally {
      setActionLoading(false);
    }
  };

  /**
   * Toggles wishlist status for a product.
   * If already wishlisted, removes it; otherwise adds it.
   */
  const toggleWishlist = async (productId) => {
    const numId = Number(productId);
    const existingItemId = wishlistedProductMap.get(numId);

    if (existingItemId) {
      const res = await removeFromWishlist(existingItemId);
      return { ...res, isWishlisted: false };
    } else {
      const res = await addToWishlist(numId);
      return { ...res, isWishlisted: true };
    }
  };

  const wishlistCount = wishlist ? wishlist.item_count : 0;

  const value = {
    wishlist,
    wishlistCount,
    loading,
    actionLoading,
    error,
    isWishlisted,
    getWishlistItemId,
    refreshWishlist,
    addToWishlist,
    removeFromWishlist,
    toggleWishlist,
  };

  return <WishlistContext.Provider value={value}>{children}</WishlistContext.Provider>;
};

export const useWishlist = () => {
  const context = useContext(WishlistContext);
  if (!context) {
    throw new Error('useWishlist must be used within a WishlistProvider');
  }
  return context;
};

export default WishlistContext;
