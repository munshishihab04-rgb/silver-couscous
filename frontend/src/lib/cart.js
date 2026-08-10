import { createContext, useContext, useEffect, useMemo, useState } from "react";

const CartContext = createContext(null);

const load = (key, fallback) => {
  try { const v = JSON.parse(localStorage.getItem(key)); return v ?? fallback; } catch { return fallback; }
};
const save = (key, val) => localStorage.setItem(key, JSON.stringify(val));

export function CartProvider({ children }) {
  const [items, setItems] = useState(() => load("lp_cart", []));
  const [compare, setCompare] = useState(() => load("lp_compare", []));
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => save("lp_cart", items), [items]);
  useEffect(() => save("lp_compare", compare), [compare]);

  const addItem = (product, variant, qty = 1, extra = {}) => {
    setItems(prev => {
      const key = `${product.slug}::${variant.id}${extra.bundleId ? "::" + extra.bundleId : ""}`;
      const idx = prev.findIndex(x => x.key === key);
      if (idx >= 0) {
        const next = [...prev]; next[idx] = { ...next[idx], qty: next[idx].qty + qty }; return next;
      }
      return [...prev, {
        key, slug: product.slug, name: product.name, brand: product.brand,
        mark: product.mark, colorKey: product.colorKey,
        variantId: variant.id, edition: variant.edition,
        duration_months: variant.duration_months, devices: variant.devices,
        price: extra.unitPrice ?? variant.price_eur,
        listPrice: extra.listPrice ?? variant.price_eur,
        bundleId: extra.bundleId || null,
        bundleLabel: extra.bundleLabel || null,
        qty,
      }];
    });
    setDrawerOpen(true);
  };

  const addBundle = (previewItems, bundleId, bundleLabel, discountPct) => {
    const factor = 1 - (discountPct || 0);
    setItems(prev => {
      const next = [...prev];
      for (const it of previewItems) {
        const unit = Math.round(it.price_eur * factor * 100) / 100;
        const key = `${it.product_slug}::${it.variant_id}::${bundleId}`;
        const existing = next.findIndex(x => x.key === key);
        if (existing >= 0) {
          next[existing] = { ...next[existing], qty: next[existing].qty + 1 };
        } else {
          next.push({
            key, slug: it.product_slug, name: it.product_name, brand: it.brand,
            mark: it.mark, colorKey: it.colorKey,
            variantId: it.variant_id, edition: it.edition,
            duration_months: it.duration_months, devices: it.devices,
            price: unit, listPrice: it.price_eur,
            bundleId, bundleLabel, qty: 1,
          });
        }
      }
      return next;
    });
    setDrawerOpen(true);
  };
  const removeItem = (key) => setItems(prev => prev.filter(x => x.key !== key));
  const setQty = (key, qty) => setItems(prev => prev.map(x => x.key === key ? { ...x, qty: Math.max(1, qty) } : x));
  const clear = () => setItems([]);

  const addCompare = (product) => setCompare(prev => {
    if (prev.find(p => p.slug === product.slug)) return prev;
    return [...prev, product].slice(0, 3);
  });
  const removeCompare = (slug) => setCompare(prev => prev.filter(p => p.slug !== slug));

  const subtotal = useMemo(() => items.reduce((s, x) => s + x.price * x.qty, 0), [items]);
  const count = useMemo(() => items.reduce((s, x) => s + x.qty, 0), [items]);

  return (
    <CartContext.Provider value={{
      items, subtotal, count, addItem, addBundle, removeItem, setQty, clear,
      compare, addCompare, removeCompare,
      drawerOpen, setDrawerOpen,
    }}>{children}</CartContext.Provider>
  );
}

export const useCart = () => useContext(CartContext);
