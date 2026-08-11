import axios from "axios";

const BASE = process.env.REACT_APP_BACKEND_URL;
export const API = `${BASE}/api`;

export const http = axios.create({ baseURL: API });

export const api = {
  categories: () => http.get("/categories").then(r => r.data),
  needs: () => http.get("/needs").then(r => r.data),
  families: () => http.get("/families").then(r => r.data),
  family: (slug) => http.get(`/families/${slug}`).then(r => r.data),
  products: (params) => http.get("/products", { params }).then(r => r.data),
  product: (slug) => http.get(`/products/${slug}`).then(r => r.data),
  related: (slug) => http.get(`/related/${slug}`).then(r => r.data),
  createOrder: (payload) => http.post("/orders", payload).then(r => r.data),
  getOrder: (ref, token) => http.get(`/orders/${ref}`, { headers: { "X-Order-Token": token } }).then(r => r.data),
  support: (payload) => http.post("/support", payload).then(r => r.data),
  formChallenge: (purpose) => http.get(`/security/form-challenge/${purpose}`).then(r => r.data),
  bundleConfig: () => http.get("/bundle/config").then(r => r.data),
  bundlePresetNuovoPc: () => http.get("/bundle/preset/nuovo-pc").then(r => r.data),
  bundlePreview: (payload) => http.post("/bundle/preview", payload).then(r => r.data),
};
