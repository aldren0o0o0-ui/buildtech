import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import AdminLayout from '../layouts/AdminLayout';

// Shared Pages
import HomePage from '../pages/HomePage';
import UnauthorizedPage from '../pages/UnauthorizedPage';

// Feature Pages & Guards
import { LoginPage, RegisterPage, ProtectedRoute, AdminRoute } from '../features/auth';
import { AccountPage } from '../features/account';
import { AdminDashboardPage } from '../features/admin';
import { AdminCategoriesPage, AdminBrandsPage } from '../features/catalog';
import { ProductsPage, ProductDetailPage, AdminProductsPage } from '../features/products';
import { AdminInventoryPage } from '../features/inventory';
import { CartPage } from '../features/cart';
import { WishlistPage } from '../features/wishlist';
import { AddressesPage } from '../features/addresses';
import { CheckoutPage } from '../features/checkout';
import {
  OrderConfirmationPage,
  OrdersPage,
  OrderDetailPage,
  AdminOrdersPage,
  AdminOrderDetailPage,
} from '../features/orders';
import { AdminReviewsPage } from '../features/reviews';
import { CompatibilityCheckerPage } from '../features/compatibility';

export const AppRoutes = () => {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        {/* Public Storefront Routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/products/:slug" element={<ProductDetailPage />} />
        <Route path="/compatibility" element={<CompatibilityCheckerPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />

        {/* Protected Customer Routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/account" element={<AccountPage />} />
          <Route path="/account/addresses" element={<AddressesPage />} />
          <Route path="/cart" element={<CartPage />} />
          <Route path="/wishlist" element={<WishlistPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/orders" element={<OrdersPage />} />
          <Route path="/orders/:orderNumber" element={<OrderDetailPage />} />
          <Route path="/orders/:orderNumber/confirmation" element={<OrderConfirmationPage />} />
        </Route>



        {/* Protected Admin Routes */}
        <Route element={<AdminRoute />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin" element={<AdminDashboardPage />} />
            <Route path="/admin/orders" element={<AdminOrdersPage />} />
            <Route path="/admin/orders/:orderId" element={<AdminOrderDetailPage />} />
            <Route path="/admin/inventory" element={<AdminInventoryPage />} />
            <Route path="/admin/products" element={<AdminProductsPage />} />
            <Route path="/admin/categories" element={<AdminCategoriesPage />} />
            <Route path="/admin/brands" element={<AdminBrandsPage />} />
            <Route path="/admin/reviews" element={<AdminReviewsPage />} />
          </Route>
        </Route>

        {/* Catch-all Redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
};

export default AppRoutes;
