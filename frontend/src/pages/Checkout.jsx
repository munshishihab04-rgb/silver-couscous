import { useState, useEffect } from "react";
import { useCart } from "../lib/cart";
import { useLang, money } from "../lib/i18n";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { trackEvent } from "../lib/tracking";
import { toast } from "sonner";
import { AlertTriangle, Check, ShieldCheck } from "lucide-react";

export default function Checkout() {
  const { items, subtotal, clear } = useCart();
  const { lang, t } = useLang();
  const nav = useNavigate();
  const [step, setStep] = useState(items.length ? 1 : 0);
  const [form, setForm] = useState({ email: "", first_name: "", last_name: "", country: "IT", company: "", vat: "" });
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (items.length > 0 && !order) {
      trackEvent({ event_type: "checkout_start", value_eur: subtotal });
    }
    // eslint-disable-next-line
  }, []);

  const canProceed1 = form.email && form.first_name && form.last_name && form.country;

  if (items.length === 0 && !order) {
    return (
      <div className="max-w-[720px] mx-auto px-6 py-24 text-center" data-testid="checkout-empty">
        <h1 className="font-display text-3xl mb-3">{t.cart.empty}</h1>
        <Link to="/catalog" className="pill-btn bg-white text-black hover:bg-zinc-200">{t.cart.keepShopping}</Link>
      </div>
    );
  }

  const confirm = async () => {
    setLoading(true);
    try {
      const payload = {
        email: form.email, first_name: form.first_name, last_name: form.last_name,
        country: form.country, company: form.company || null, vat: form.vat || null,
        items: items.map(it => ({
          product_slug: it.slug, product_name: it.name,
          variant_id: it.variantId,
          variant_label: `${it.edition} · ${it.duration_months === 0 ? t.product.perpetual : it.duration_months + " " + t.product.months} · ${it.devices} ${it.devices === 1 ? t.product.device : t.product.devices}`,
          quantity: it.qty, unit_price_eur: it.price,
        })),
        subtotal_eur: subtotal, total_eur: subtotal, language: lang,
      };
      const res = await api.createOrder(payload);
      setOrder(res);
      setStep(3);
      trackEvent({ event_type: "order_confirmed", value_eur: subtotal, extra: { reference: res.reference } });
      clear();
    } catch (e) {
      toast.error(lang === "it" ? "Errore, riprova" : "Something went wrong, try again");
    } finally {
      setLoading(false);
    }
  };

  const Stepper = () => (
    <div className="flex items-center gap-3 mb-10">
      {[t.checkout.step1, t.checkout.step2, t.checkout.step3].map((label, i) => {
        const idx = i + 1, active = step === idx, done = step > idx;
        return (
          <div key={label} className="flex items-center gap-3">
            <div className={`w-7 h-7 rounded-full border flex items-center justify-center text-xs font-mono transition-colors ${done ? "bg-white text-black border-white" : active ? "border-white text-white" : "border-white/15 text-zinc-500"}`}>
              {done ? <Check size={14} /> : idx}
            </div>
            <span className={`text-sm font-heading ${active ? "text-white" : "text-zinc-500"}`}>{label}</span>
            {i < 2 && <div className="w-8 h-px bg-white/10" />}
          </div>
        );
      })}
    </div>
  );

  return (
    <div className="max-w-[1200px] mx-auto px-6 md:px-10 py-12" data-testid="checkout-page">
      <p className="label-eyebrow mb-2">Checkout</p>
      <h1 className="font-display text-4xl md:text-5xl tracking-tight mb-10">{t.checkout.title}</h1>

      <Stepper />

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-10">
        <div>
          {step === 1 && (
            <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-6 md:p-8">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[
                  ["email", t.checkout.email, "email"],
                  ["first_name", t.checkout.firstName, "text"],
                  ["last_name", t.checkout.lastName, "text"],
                  ["country", t.checkout.country, "text"],
                  ["company", t.checkout.companyOpt, "text"],
                  ["vat", t.checkout.vatOpt, "text"],
                ].map(([k, label, type]) => (
                  <label key={k} className="block">
                    <span className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-1 block">{label}</span>
                    <input data-testid={`checkout-field-${k}`} type={type} value={form[k]} onChange={e => setForm({ ...form, [k]: e.target.value })}
                      className="w-full bg-black border border-white/10 rounded-md px-3 py-2.5 text-white focus:outline-none focus:border-white/30 transition-colors" />
                  </label>
                ))}
              </div>
              <div className="mt-6 flex flex-col sm:flex-row gap-3">
                <Link to="/catalog" data-testid="checkout-back-cart" className="pill-btn border border-white/20 text-white hover:bg-white/5">{t.checkout.backToCart}</Link>
                <button data-testid="checkout-next-1" disabled={!canProceed1} onClick={() => setStep(2)}
                  className="pill-btn bg-white text-black hover:bg-zinc-200 disabled:opacity-40 disabled:cursor-not-allowed">Continue</button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-6 md:p-8">
              <div className="flex items-start gap-3 rounded-lg border border-orange-500/30 bg-orange-500/[0.06] p-4 mb-6">
                <AlertTriangle size={18} className="text-orange-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-orange-200 font-heading">Demo Mode</p>
                  <p className="text-sm text-orange-100/70 mt-1">{t.checkout.demoNotice}</p>
                </div>
              </div>
              <div className="border border-dashed border-white/10 rounded-lg p-6 flex items-center gap-4">
                <ShieldCheck size={24} className="text-zinc-500" />
                <div className="text-sm text-zinc-400">
                  {lang === "it" ? "Nessuna carta o dettaglio di pagamento verrà richiesto." : "No card or payment details will be requested."}
                </div>
              </div>
              <div className="mt-6 flex flex-col sm:flex-row gap-3">
                <button onClick={() => setStep(1)} className="pill-btn border border-white/20 text-white hover:bg-white/5">Back</button>
                <button data-testid="checkout-confirm-order" onClick={confirm} disabled={loading}
                  className="pill-btn bg-white text-black hover:bg-zinc-200 disabled:opacity-40">
                  {loading ? "..." : t.checkout.pay}
                </button>
              </div>
            </div>
          )}

          {step === 3 && order && (
            <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-8 md:p-14 text-center" data-testid="checkout-success">
              <div className="w-14 h-14 rounded-full bg-white text-black flex items-center justify-center mx-auto"><Check size={22} /></div>
              <h2 className="font-display text-4xl md:text-5xl tracking-tight mt-6">{t.checkout.thanks}</h2>
              <p className="text-zinc-400 mt-3 max-w-md mx-auto">{t.checkout.thanksSub}</p>
              <div className="mt-8 inline-flex flex-col gap-1 border border-white/10 rounded-xl px-6 py-4">
                <span className="label-eyebrow">{t.checkout.reference}</span>
                <span data-testid="order-reference" className="font-mono text-white text-lg">{order.reference}</span>
              </div>
              <div className="mt-8">
                <Link to="/" className="pill-btn bg-white text-black hover:bg-zinc-200">{t.checkout.backHome}</Link>
              </div>
            </div>
          )}
        </div>

        {/* Summary */}
        <aside className="rounded-xl border border-white/10 bg-[#0B0B0D] p-6 h-fit lg:sticky lg:top-24">
          <p className="label-eyebrow mb-4">Order summary</p>
          {order ? (
            <p className="text-sm text-zinc-500">{lang === "it" ? "Ordine completato" : "Order complete"}</p>
          ) : (
            <>
              <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                {items.map(it => (
                  <div key={it.key} className="flex gap-3 items-start pb-3 border-b border-white/5">
                    <div className={`w-11 h-11 shrink-0 rounded mesh-${it.colorKey} flex items-center justify-center`}>
                      <span className="font-display font-bold text-white text-sm">{it.mark}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-sm truncate">{it.name}</p>
                      <p className="text-xs text-zinc-500">{it.edition} × {it.qty}</p>
                    </div>
                    <p className="text-white text-sm font-mono">{money(it.price * it.qty)}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex items-center justify-between">
                <span className="text-sm text-zinc-400">{t.cart.subtotal}</span>
                <span className="font-display text-white text-2xl">{money(subtotal)}</span>
              </div>
              <p className="text-xs text-zinc-600 mt-1">{t.cart.vat}</p>
            </>
          )}
        </aside>
      </div>
    </div>
  );
}
