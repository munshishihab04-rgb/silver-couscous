import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../lib/api";
import { useLang } from "../lib/i18n";
import ProductCard from "../components/ProductCard";
import { SlidersHorizontal, X } from "lucide-react";

export default function Catalog() {
  const { lang, t } = useLang();
  const [sp, setSp] = useSearchParams();
  const [cats, setCats] = useState([]);
  const [all, setAll] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mobileFilters, setMobileFilters] = useState(false);

  const q = sp.get("q") || "";
  const category = sp.get("category") || "";
  const need = sp.get("need") || "";
  const platform = sp.get("platform") || "";
  const brand = sp.get("brand") || "";
  const license_type = sp.get("license_type") || "";
  const sort = sp.get("sort") || "featured";
  const max_price = sp.get("max_price") || "";

  useEffect(() => { api.categories().then(setCats); }, []);

  useEffect(() => {
    setLoading(true);
    const params = { q, category, need, platform, brand, license_type, sort };
    if (max_price) params.max_price = max_price;
    Object.keys(params).forEach(k => !params[k] && delete params[k]);
    api.products(params).then(r => { setAll(r.items); setLoading(false); });
  }, [q, category, need, platform, brand, license_type, sort, max_price]);

  const brands = useMemo(() => Array.from(new Set(all.map(p => p.brand))).sort(), [all]);
  const platforms = ["Windows", "macOS", "iOS", "Android", "Linux", "Windows Server"];
  const licenseTypes = ["Perpetua", "Abbonamento"];

  const update = (key, value) => {
    const next = new URLSearchParams(sp);
    if (value) next.set(key, value); else next.delete(key);
    setSp(next);
  };
  const clear = () => setSp(new URLSearchParams());

  const Filters = () => (
    <div className="space-y-8">
      <div>
        <p className="label-eyebrow mb-3">{t.catalog.category}</p>
        <div className="flex flex-col gap-1">
          <button data-testid="filter-cat-all" onClick={() => update("category", "")}
            className={`text-left text-sm py-1 transition-colors ${!category ? "text-white" : "text-zinc-500 hover:text-white"}`}>All</button>
          {cats.map(c => (
            <button key={c.key} data-testid={`filter-cat-${c.key}`} onClick={() => update("category", c.key)}
              className={`text-left text-sm py-1 transition-colors ${category === c.key ? "text-white" : "text-zinc-500 hover:text-white"}`}>
              {lang === "it" ? c.name_it : c.name_en}
            </button>
          ))}
        </div>
      </div>
      <div>
        <p className="label-eyebrow mb-3">{t.catalog.platform}</p>
        <div className="flex flex-wrap gap-2">
          {platforms.map(p => (
            <button key={p} data-testid={`filter-platform-${p}`} onClick={() => update("platform", platform === p ? "" : p)}
              className={`chip ${platform === p ? "!bg-white !text-black !border-white" : ""}`}>{p}</button>
          ))}
        </div>
      </div>
      <div>
        <p className="label-eyebrow mb-3">{t.catalog.brand}</p>
        <div className="flex flex-wrap gap-2">
          {brands.slice(0, 12).map(b => (
            <button key={b} onClick={() => update("brand", brand === b ? "" : b)}
              className={`chip ${brand === b ? "!bg-white !text-black !border-white" : ""}`}>{b}</button>
          ))}
        </div>
      </div>
      <div>
        <p className="label-eyebrow mb-3">{t.catalog.licenseType}</p>
        <div className="flex flex-wrap gap-2">
          {licenseTypes.map(l => (
            <button key={l} onClick={() => update("license_type", license_type === l ? "" : l)}
              className={`chip ${license_type === l ? "!bg-white !text-black !border-white" : ""}`}>{l}</button>
          ))}
        </div>
      </div>
      <button onClick={clear} data-testid="filter-clear" className="text-xs font-mono uppercase tracking-widest text-zinc-500 hover:text-white transition-colors">
        <X size={12} className="inline mr-1" /> {t.catalog.clear}
      </button>
    </div>
  );

  return (
    <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-12" data-testid="catalog-page">
      <div className="flex items-end justify-between flex-wrap gap-4 mb-8">
        <div>
          <p className="label-eyebrow mb-2">Catalog</p>
          <h1 className="font-display text-4xl md:text-5xl tracking-tight">{t.catalog.title}</h1>
          <p data-testid="catalog-results-count" className="text-sm text-zinc-500 mt-2">{all.length} {t.catalog.results}</p>
        </div>
        <div className="flex items-center gap-2">
          <select data-testid="catalog-sort" value={sort} onChange={e => update("sort", e.target.value)}
            className="bg-[#0B0B0D] border border-white/10 rounded-full px-4 py-2 text-sm text-white focus:outline-none focus:border-white/30">
            <option value="featured">{t.catalog.sortFeatured}</option>
            <option value="price_asc">{t.catalog.sortPriceAsc}</option>
            <option value="price_desc">{t.catalog.sortPriceDesc}</option>
            <option value="name">{t.catalog.sortName}</option>
          </select>
          <button onClick={() => setMobileFilters(true)} className="md:hidden pill-btn border border-white/20 text-white text-xs">
            <SlidersHorizontal size={14} /> {t.catalog.filters}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[240px_1fr] gap-10">
        <aside className="hidden md:block sticky top-24 self-start"><Filters /></aside>

        {mobileFilters && (
          <div className="fixed inset-0 z-50 bg-black md:hidden overflow-y-auto p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="font-display text-2xl">{t.catalog.filters}</h2>
              <button onClick={() => setMobileFilters(false)} className="text-zinc-400"><X size={22} /></button>
            </div>
            <Filters />
            <button onClick={() => setMobileFilters(false)} className="pill-btn bg-white text-black w-full mt-8">Ok</button>
          </div>
        )}

        <div>
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(6)].map((_, i) => <div key={i} className="rounded-xl border border-white/10 bg-[#0B0B0D] h-80 animate-pulse" />)}
            </div>
          ) : all.length === 0 ? (
            <div className="border border-dashed border-white/10 rounded-xl p-16 text-center text-zinc-500">{t.catalog.empty}</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {all.map(p => <ProductCard key={p.slug} product={p} />)}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
