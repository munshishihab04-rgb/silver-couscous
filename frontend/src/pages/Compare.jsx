import { useCart } from "../lib/cart";
import { useLang, money } from "../lib/i18n";
import { Link } from "react-router-dom";
import { Trash2, Layers } from "lucide-react";
import { productPrice } from "../lib/productPricing";

export default function Compare() {
  const { compare, removeCompare, addItem } = useCart();
  const { lang, t } = useLang();

  if (compare.length === 0) {
    return (
      <div className="max-w-[900px] mx-auto px-6 py-24 text-center" data-testid="compare-empty">
        <Layers size={32} className="mx-auto text-zinc-500 mb-4" />
        <h1 className="font-display text-3xl md:text-4xl mb-3">{t.compare.title}</h1>
        <p className="text-zinc-500 mb-6">{t.compare.empty}</p>
        <Link to="/catalog" className="pill-btn bg-white text-black hover:bg-zinc-200">{t.compare.cta}</Link>
      </div>
    );
  }

  const row = (label, render) => (
    <tr className="border-b border-white/5">
      <th className="text-left py-4 pr-4 label-eyebrow align-top w-40">{label}</th>
      {compare.map(p => <td key={p.slug} className="py-4 px-4 align-top text-zinc-300 text-sm">{render(p)}</td>)}
    </tr>
  );

  return (
    <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-12" data-testid="compare-page">
      <p className="label-eyebrow mb-2">Compare</p>
      <h1 className="font-display text-4xl md:text-5xl tracking-tight mb-8">{t.compare.title}</h1>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px]">
          <thead>
            <tr className="border-b border-white/10">
              <th></th>
              {compare.map(p => (
                <th key={p.slug} className="p-4 text-left align-top">
                  <div className={`w-full aspect-[4/3] rounded-xl border border-white/10 mesh-${p.colorKey} flex items-center justify-center mb-3 relative overflow-hidden`}>
                    <div className="absolute inset-0 grain" />
                    <span className="font-display font-bold text-white text-5xl">{p.mark}</span>
                  </div>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="label-eyebrow">{p.brand}</p>
                      <p className="font-display text-white text-lg leading-tight">{p.name}</p>
                    </div>
                    <button data-testid={`compare-remove-${p.slug}`} onClick={() => removeCompare(p.slug)} className="text-zinc-500 hover:text-red-400"><Trash2 size={14} /></button>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {row(t.compare.cols.brand, p => p.brand)}
            {row(t.compare.cols.platforms, p => p.platforms.join(", "))}
            {row(t.compare.cols.licenseType, p => p.licenseType)}
            {row(t.compare.cols.startingAt, p => productPrice(p) === null ? (lang === "it" ? "In verifica" : "Under review") : money(productPrice(p)))}
            {row(t.compare.cols.variants, p => `${p.variants.length}`)}
            {row(t.compare.cols.features, p => (
              <ul className="space-y-1 text-xs">{(lang === "it" ? p.features_it : p.features_en).slice(0, 4).map((f, i) => <li key={i}>· {f}</li>)}</ul>
            ))}
            <tr>
              <td></td>
              {compare.map(p => (
                <td key={p.slug} className="p-4">
                  <button disabled={!p.purchasable} onClick={() => p.purchasable && addItem(p, p.variants[0])} className="pill-btn bg-white text-black hover:bg-zinc-200 w-full text-sm disabled:bg-zinc-700 disabled:text-zinc-300 disabled:cursor-not-allowed">{p.purchasable ? t.compare.add : (lang === "it" ? "Non disponibile" : "Unavailable")}</button>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
