import { Suspense, lazy } from "react";
import { Routes, Route } from "react-router-dom";
import { AdminAuthProvider } from "./auth.jsx";

const AdminLayout = lazy(() => import("./Layout.jsx"));
const AdminLogin = lazy(() => import("./Login.jsx"));
const AdminDashboard = lazy(() => import("./Dashboard.jsx"));
const AdminProducts = lazy(() => import("./Products.jsx"));
const AdminCustomers = lazy(() => import("./Customers.jsx"));
const AdminTickets = lazy(() => import("./Tickets.jsx"));
const AdminPages = lazy(() => import("./Pages.jsx"));
const AdminSettings = lazy(() => import("./Settings.jsx"));
const AdminAnalytics = lazy(() => import("./Analytics.jsx"));

export default function AdminApp() {
  return (
    <AdminAuthProvider>
      <Suspense fallback={<div className="min-h-screen bg-[#050505] text-white flex items-center justify-center">…</div>}>
        <Routes>
          <Route path="/login" element={<AdminLogin />} />
          <Route element={<AdminLayout />}>
            <Route index element={<AdminDashboard />} />
            <Route path="products" element={<AdminProducts />} />
            <Route path="customers" element={<AdminCustomers />} />
            <Route path="tickets" element={<AdminTickets />} />
            <Route path="pages" element={<AdminPages />} />
            <Route path="analytics" element={<AdminAnalytics />} />
            <Route path="settings" element={<AdminSettings />} />
          </Route>
        </Routes>
      </Suspense>
    </AdminAuthProvider>
  );
}
