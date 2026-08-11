import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { useLang, money } from "../lib/i18n";
import { useCart } from "../lib/cart";
import { toast } from "sonner";
import { Link, useNavigate } from "react-router-dom";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from "../components/ui/dialog";
import {
  Check, Plus, Sparkles, ArrowRight, X, Layers, Wand2, ChevronDown,
} from "lucide-react";

const BUNDLE_ID = "nuovo-pc";
const BUNDLE_LABEL_IT = "Nuovo PC";
const BUNDLE_LABEL_EN = "New PC";

export default function BundleBuilder() {
  const { lang, t } = useLang();
  const { addBundle } = useCart();
  const nav = useNavigate();

  const [config, setConfig] = useState(null);
  const [productsByCat, setProductsByCat] = useState({});
  const [picks, setPicks] = useState({});
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [openSlot, setOpenSlot] = useState(null);

  // load config
  useEffect(() => {
    (async () => {
      const cfg = await api.bundleConfig();
      setConfig(cfg);
      const cats = Array.from(new Set(cfg.slots.flatMap(s => s.categories)));
      const map = {};
      await Promise.all(cats.map(async c => {
        const r = await api.products({ category: c, sort: "price_asc" });
        map[c] = r.items.filter(product => product.purchasable);
      }));
      setProductsByCat(map);
    })();
  }, []);

  // fetch preview when picks change
  useEffect(() => {
    const selections = Object.values(picks).filter(Boolean);
    if (selections.length === 0) { setPreview(null); return; }
    setLoading(true);
    api.bundlePreview({ selections })
      .then(setPreview)
      .finally(() => setLoading(false));
  }, [picks]);

  const applyPreset = async () => {
    const r = await api.bundlePresetNuovoPc();
    const next = {};
    // Best-effort slotting by category
    for (const sel of r.selections) {
      const p = productsByCat && Object.values(productsByCat).flat().find(x => x.slug === sel.product_slug);
      if (!p) continue;
      const slot = config.slots.find(s => s.categories.includes(p.category));
      if (slot) next[slot.key] = { ...sel };
    }
    setPicks(next);
    toast.success(lang === "it" ? "Preset applicato" : "Preset applied");
  };

  const clearAll = () => setPicks({});

  const setPick = (slotKey, product, variant) => {
    setPicks(prev => ({ ...prev, [slotKey]: { product_slug: product.slug, variant_id: variant.id } }));
    setOpenSlot(null);
  };
  const removePick = (slotKey) => {
    setPicks(prev => { const n = { ...prev }; delete n[slotKey]; return n; });
  };

  const findLine = (slotKey) => {
    if (!preview) return null;
    const p = picks[slotKey]; if (!p) return null;
    return preview.items.find(x => x.product_slug === p.product_slug && x.variant_id === p.variant_id);
  };

  const canAdd = preview && preview.count >= 1;

  const doAddAll = () => {
    if (!preview || preview.items.length === 0) return;
    const label = lang === "it" ? BUNDLE_LABEL_IT : BUNDLE_LABEL_EN;
    addBundle(preview.items, BUNDLE_ID, label, preview.discount_pct);
    toast.success(lang === "it" ? "Bundle aggiunto al carrello" : "Bundle added to cart");
    setTimeout(() => nav("/checkout"), 600);
  };

  if (!config) {
    return <div className="max-w-[1400px] mx-auto px-6 py-24 text-center text-zinc-500">Loading...</div>;
  }

  return (
    <div className="text-white" data-testid="bundle-page">
      {/* HERO */}
      <section className="relative overflow-hidden border-b border-white/10">
        <div className="absolute inset-0 dashed-grid opacity-40" />
        <div className="absolute -top-40 -right-40 w-[600px] h-[600px] rounded-full bg-blue-500/10 blur-3xl" />
        <div className="absolute inset-0 grain" />
        <div className="relative max-w-[1400px] mx-auto px-6 md:px-10 pt-16 md:pt-24 pb-14">
          <div className="inline-flex items-center gap-2 chip mb-6">
            <Sparkles size={12} className="text-blue-300" /> {t.bundle.eyebrow}
          </div>
          <h1 className="font-display font-medium tracking-tighter text-white" style={{ fontSize: 'clamp(44px, 8vw, 120px)', lineHeight: 0.95 }}>
            {t.bundle.title}<br /><span className="text-zinc-500">{t.bundle.title2}</span>
          </h1>
          <p className="mt-6 text-zinc-400 text-lg max-w-2xl leading-relaxed">{t.bundle.sub}</p>

          <div className="mt-8 flex flex-wrap gap-3">
            <button data-testid="bundle-preset-btn" onClick={applyPreset}
              className="pill-btn bg-white text-black hover:bg-zinc-200">
              <Wand2 size={16} /> {t.bundle.preset}: {t.bundle.presetName}
            </button>
            <button data-testid="bundle-clear-btn" onClick={clearAll}
              className="pill-btn border border-white/20 text-white hover:bg-white/5">
              <X size={14} /> {t.bundle.startEmpty}
            </button>
          </div>

          {/* Discount tiers */}
          <div className="mt-10 flex flex-wrap items-center gap-3">
            <p className="label-eyebrow">{t.bundle.tiersLabel}</p>
            {t.bundle.tiers.map((tier, i) => {
              const active = preview && preview.count >= tier.n;
              return (
                <span key={i} className={`chip transition-colors ${active ? "!bg-white !text-black !border-white" : ""}`}>
                  {tier.n}+ · {tier.d}
                </span>
              );
            })}
          </div>
        </div>
      </section>

      {/* BUILDER */}
      <section className="max-w-[1400px] mx-auto px-6 md:px-10 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-10">
          {/* Slots */}
          <div className="space-y-3">
            {config.slots.map((slot, i) => {
              const pick = picks[slot.key];
              const line = findLine(slot.key);
              const catProducts = slot.categories.flatMap(c => productsByCat[c] || []);
              return (
                <div key={slot.key} data-testid={`bundle-slot-${slot.key}`}
                  className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5 md:p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-9 h-9 shrink-0 rounded-full border border-white/15 flex items-center justify-center font-mono text-sm text-zinc-400">
                      {i + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-heading text-white text-lg">{lang === "it" ? slot.title_it : slot.title_en}</p>
                        {slot.required && <span className="chip !text-[10px] !py-0.5">{lang === "it" ? "Richiesto" : "Required"}</span>}
                      </div>
                      <p className="text-xs text-zinc-500 mt-0.5">{t.bundle.steps[i] || ""} · {lang === "it" ? slot.hint_it : slot.hint_en}</p>

                      {pick && line ? (
                        <div className="mt-4 flex items-center gap-3">
                          <div className={`w-14 h-14 shrink-0 rounded-md mesh-${line.colorKey} flex items-center justify-center`}>
                            <span className="font-display font-bold text-white text-lg">{line.mark}</span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="label-eyebrow">{line.brand}</p>
                            <p className="text-white font-heading text-sm leading-tight">{line.product_name}</p>
                            <p className="text-xs text-zinc-500 mt-0.5">
                              {line.edition} · {line.duration_months === 0 ? t.product.perpetual : `${line.duration_months} ${t.product.months}`} · {line.devices} {line.devices === 1 ? t.product.device : t.product.devices}
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="font-display text-white text-lg">{money(line.price_eur)}</span>
                            <button data-testid={`bundle-change-${slot.key}`} onClick={() => setOpenSlot(slot.key)}
                              className="pill-btn !py-1.5 !px-3 !text-xs border border-white/20 text-white hover:bg-white/5">{t.bundle.change}</button>
                            <button data-testid={`bundle-remove-${slot.key}`} onClick={() => removePick(slot.key)}
                              className="text-zinc-500 hover:text-red-400 transition-colors"><X size={16} /></button>
                          </div>
                        </div>
                      ) : (
                        <button data-testid={`bundle-pick-${slot.key}`} onClick={() => setOpenSlot(slot.key)}
                          className="mt-4 w-full text-left rounded-lg border border-dashed border-white/15 hover:border-white/30 hover:bg-white/[0.02] p-4 flex items-center justify-between transition-colors">
                          <div className="flex items-center gap-3 text-zinc-400">
                            <Plus size={16} />
                            <span className="text-sm">{t.bundle.slotEmpty}</span>
                          </div>
                          <ChevronDown size={16} className="text-zinc-500" />
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Picker dialog */}
                  <Dialog open={openSlot === slot.key} onOpenChange={(o) => setOpenSlot(o ? slot.key : null)}>
                    <DialogContent className="max-w-2xl bg-[#0A0A0C] border border-white/10 text-white p-0 overflow-hidden">
                      <DialogHeader className="px-6 pt-6 pb-4 border-b border-white/10">
                        <DialogTitle className="font-display text-2xl">{lang === "it" ? slot.title_it : slot.title_en}</DialogTitle>
                      </DialogHeader>
                      <div className="max-h-[70vh] overflow-y-auto divide-y divide-white/5">
                        {catProducts.length === 0 && (
                          <p className="px-6 py-8 text-sm text-zinc-500">{lang === "it" ? "Nessun prodotto approvato e acquistabile in questa categoria." : "No approved, purchasable product in this category."}</p>
                        )}
                        {catProducts.map(p => (
                          <div key={p.slug} className="px-6 py-4">
                            <div className="flex items-center gap-4">
                              <div className={`w-12 h-12 shrink-0 rounded-md mesh-${p.colorKey} flex items-center justify-center`}>
                                <span className="font-display font-bold text-white">{p.mark}</span>
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="label-eyebrow">{p.brand}</p>
                                <p className="font-heading text-white text-sm leading-tight">{p.name}</p>
                                <p className="text-xs text-zinc-500 mt-0.5 line-clamp-1">{lang === "it" ? p.tagline_it : p.tagline_en}</p>
                              </div>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-2">
                              {p.variants.map(v => {
                                const dur = v.duration_months === 0 ? t.product.perpetual : `${v.duration_months} ${t.product.months}`;
                                const dev = `${v.devices} ${v.devices === 1 ? t.product.device : t.product.devices}`;
                                return (
                                  <button key={v.id} data-testid={`bundle-variant-${p.slug}-${v.id}`}
                                    onClick={() => setPick(slot.key, p, v)}
                                    className="px-3 py-1.5 rounded-full border border-white/15 hover:border-white text-xs text-zinc-300 hover:text-white transition-colors">
                                    {v.edition} · {dur} · {dev} · <span className="font-mono text-white">{money(v.price_eur)}</span>
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        ))}
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              );
            })}
          </div>

          {/* Summary */}
          <aside className="lg:sticky lg:top-24 self-start">
            <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-6 relative overflow-hidden">
              <div className="absolute inset-0 grain" />
              <div className="relative">
                <p className="label-eyebrow mb-4">{t.bundle.summary}</p>

                {!preview || preview.count === 0 ? (
                  <div className="border border-dashed border-white/10 rounded-lg p-8 text-center text-zinc-500 text-sm">
                    {t.bundle.slotEmpty}
                  </div>
                ) : (
                  <div className="space-y-2">
                    {preview.items.map(it => (
                      <div key={it.variant_id} className="flex items-center gap-3 py-2 border-b border-white/5">
                        <div className={`w-8 h-8 shrink-0 rounded mesh-${it.colorKey} flex items-center justify-center`}>
                          <span className="font-display font-bold text-white text-[11px]">{it.mark}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-white text-xs truncate">{it.product_name}</p>
                          <p className="text-[10px] text-zinc-500">{it.edition}</p>
                        </div>
                        <span className="font-mono text-sm text-white">{money(it.price_eur)}</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="mt-5 space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-zinc-400">{t.bundle.subtotal}</span>
                    <span data-testid="bundle-subtotal" className="font-mono text-white">{money(preview?.subtotal_eur || 0)}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-zinc-400">{t.bundle.discount}
                      {preview?.discount_pct ? <span className="ml-1 text-blue-300 font-mono text-xs">−{Math.round((preview.discount_pct || 0) * 100)}%</span> : null}
                    </span>
                    <span data-testid="bundle-discount" className="font-mono text-blue-300">−{money(preview?.discount_eur || 0)}</span>
                  </div>
                  <div className="flex items-end justify-between pt-3 border-t border-white/10">
                    <span className="font-heading text-white">{t.bundle.total}</span>
                    <span data-testid="bundle-total" className="font-display text-white text-3xl">{money(preview?.total_eur || 0)}</span>
                  </div>
                  {preview && preview.count === 1 && (
                    <p className="text-xs text-orange-300/80">{t.bundle.minReq}</p>
                  )}
                  {preview && preview.discount_eur > 0 && (
                    <p className="text-xs text-green-400 flex items-center gap-1"><Check size={12} /> {t.bundle.savings} {money(preview.discount_eur)}</p>
                  )}
                </div>

                <button data-testid="bundle-add-all-btn" onClick={doAddAll} disabled={!canAdd || loading}
                  className="pill-btn w-full mt-6 bg-white text-black hover:bg-zinc-200 disabled:opacity-40 disabled:cursor-not-allowed">
                  <Layers size={16} /> {t.bundle.addAll}
                </button>
                <Link to="/catalog" className="mt-3 block text-center text-xs font-mono text-zinc-500 hover:text-white transition-colors">
                  {t.cart.keepShopping} <ArrowRight size={12} className="inline ml-1" />
                </Link>
              </div>
            </div>
          </aside>
        </div>
      </section>
    </div>
  );
}
