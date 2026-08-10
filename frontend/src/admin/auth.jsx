import { createContext, useContext, useEffect, useState } from "react";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api/admin`;

const AdminAuthContext = createContext(null);

export function AdminAuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("lp_admin_token"));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) { setUser(null); setLoading(false); return; }
    axios.get(`${API}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => setUser(r.data.user))
      .catch(() => { setToken(null); localStorage.removeItem("lp_admin_token"); setUser(null); })
      .finally(() => setLoading(false));
  }, [token]);

  const login = async (email, password) => {
    const r = await axios.post(`${API}/auth/login`, { email, password });
    localStorage.setItem("lp_admin_token", r.data.token);
    setToken(r.data.token);
    setUser(r.data.user);
    return r.data.user;
  };
  const logout = () => {
    localStorage.removeItem("lp_admin_token");
    setToken(null); setUser(null);
  };

  return (
    <AdminAuthContext.Provider value={{ token, user, loading, login, logout }}>
      {children}
    </AdminAuthContext.Provider>
  );
}

export const useAdminAuth = () => useContext(AdminAuthContext);

export function adminApi(token) {
  const client = axios.create({
    baseURL: API,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return {
    dashboardOverview: (range = "7d") => client.get(`/analytics/overview?range=${range}`).then(r => r.data),
    liveAnalytics: () => client.get(`/analytics/live`).then(r => r.data),
    products: (params) => client.get(`/products`, { params }).then(r => r.data),
    product: (slug) => client.get(`/products/${slug}`).then(r => r.data),
    createProduct: (b) => client.post(`/products`, b).then(r => r.data),
    updateProduct: (slug, b) => client.patch(`/products/${slug}`, b).then(r => r.data),
    deleteProduct: (slug) => client.delete(`/products/${slug}`).then(r => r.data),
    customers: (q) => client.get(`/customers`, { params: q ? { q } : {} }).then(r => r.data),
    customer: (email) => client.get(`/customers/${encodeURIComponent(email)}`).then(r => r.data),
    orders: () => client.get(`/orders`).then(r => r.data),
    tickets: (status) => client.get(`/tickets`, { params: status ? { status } : {} }).then(r => r.data),
    updateTicket: (id, b) => client.patch(`/tickets/${id}`, b).then(r => r.data),
    pages: () => client.get(`/pages`).then(r => r.data),
    page: (slug) => client.get(`/pages/${slug}`).then(r => r.data),
    updatePage: (slug, b) => client.put(`/pages/${slug}`, b).then(r => r.data),
    settings: () => client.get(`/settings`).then(r => r.data),
    updateSettings: (b) => client.patch(`/settings`, b).then(r => r.data),
    admins: () => client.get(`/users`).then(r => r.data),
    createAdmin: (b) => client.post(`/users`, b).then(r => r.data),
    deleteAdmin: (id) => client.delete(`/users/${id}`).then(r => r.data),
  };
}
