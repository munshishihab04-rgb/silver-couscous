import { Sheet, SheetContent, SheetHeader, SheetTitle } from "./ui/sheet";
import { useCart } from "../lib/cart";
import { useLang, money } from "../lib/i18n";
import { Link } from "react-router-dom";
import { Minus, Plus, Trash2, ShoppingBag } from "lucide-react";

export default function CartDrawer() {
  const { items, subtotal, drawerOpen, setDrawerOpen, removeItem, setQty } = useCart();
  const { lang, t } = useLang();

  return (
    <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
      <SheetContent side="right" className="w-full sm:max-w-md bg-[#0A0A0C] text-white border-l border-white/10 p-0 flex flex-col">
        <SheetHeader className="px-6 pt-6 pb-4 border-b border-white/10">
          <SheetTitle className="font-display text-white text-2xl">{t.cart.title}</SheetTitle>
        </SheetHeader>

        {items.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center px-10 text-center gap-4">
            <div className="w-14 h-14 rounded-full border border-white/10 flex items-center justify-center text-zinc-500">
              <ShoppingBag size={22} />
            </div>
            <div>
              <p className="font-display text-white text-lg">{t.cart.empty}</p>
              <p className="text-sm text-zinc-500 mt-1">{t.cart.emptySub}</p>
            </div>
            <Link data-testid="cart-empty-cta" to="/catalog" onClick={() => setDrawerOpen(false)}
              className="pill-btn bg-white text-black hover:bg-zinc-200 mt-2">
              {t.cart.keepShopping}
            </Link>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto px-6 py-4 flex flex-col gap-4">
              {items.map(it => (
                <div key={it.key} data-testid={`cart-item-${it.slug}`} className="flex gap-4 pb-4 border-b border-white/5">
                  <div className={`w-16 h-16 shrink-0 rounded-md mesh-${it.colorKey} flex items-center justify-center`}>
                    <span className="font-display font-bold text-white text-xl">{it.mark}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[10px] font-mono uppercase tracking-widest text-zinc-500">{it.brand}</p>
                    <p className="font-heading text-white text-sm leading-tight">{it.name}</p>
                    <p className="text-xs text-zinc-500 mt-0.5">
                      {it.edition} · {it.duration_months === 0 ? t.product.perpetual : `${it.duration_months} ${t.product.months}`} · {it.devices} {it.devices === 1 ? t.product.device : t.product.devices}
                    </p>
                    {it.bundleId && (
                      <span className="inline-block mt-1 text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-300 border border-blue-500/30">
                        {it.bundleLabel || "Bundle"}
                      </span>
                    )}
                    <div className="flex items-center justify-between mt-2">
                      <div className="inline-flex items-center border border-white/10 rounded-full overflow-hidden">
                        <button data-testid={`qty-dec-${it.slug}`} onClick={() => setQty(it.key, it.qty - 1)} className="px-2 py-1 text-zinc-400 hover:text-white transition-colors"><Minus size={12} /></button>
                        <span className="px-2 text-sm font-mono">{it.qty}</span>
                        <button data-testid={`qty-inc-${it.slug}`} onClick={() => setQty(it.key, it.qty + 1)} className="px-2 py-1 text-zinc-400 hover:text-white transition-colors"><Plus size={12} /></button>
                      </div>
                      <div className="text-right">
                        <p className="font-display text-white">{money(it.price * it.qty)}</p>
                        {it.listPrice && it.listPrice > it.price && (
                          <p className="text-[10px] font-mono text-zinc-600 line-through">{money(it.listPrice * it.qty)}</p>
                        )}
                      </div>
                    </div>
                  </div>
                  <button data-testid={`cart-remove-${it.slug}`} onClick={() => removeItem(it.key)} className="text-zinc-500 hover:text-red-400 transition-colors self-start"><Trash2 size={14} /></button>
                </div>
              ))}
            </div>
            <div className="px-6 py-5 border-t border-white/10 bg-black">
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm text-zinc-400">{t.cart.subtotal}</p>
                <p data-testid="cart-subtotal" className="font-display text-white text-2xl">{money(subtotal)}</p>
              </div>
              <p className="text-xs text-zinc-600 mb-4">{t.cart.vat}</p>
              <Link data-testid="cart-checkout-btn" to="/checkout" onClick={() => setDrawerOpen(false)}
                className="pill-btn w-full bg-white text-black hover:bg-zinc-200">
                {t.cart.checkout}
              </Link>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
