import { Link, useLocation, useNavigate } from "react-router-dom";
import { useCart } from "../lib/cart";
import { useLang } from "../lib/i18n";
import { useSiteSettings } from "../lib/tracking";
import { ShoppingBag, Search, Menu, Layers, X, Globe } from "lucide-react";
import { useEffect, useState } from "react";

export default function Nav() {
  const nav = useNavigate();
  const loc = useLocation();
  const { count, setDrawerOpen, compare } = useCart();
  const { lang, setLang, t } = useLang();
  const { settings } = useSiteSettings();
  const [q, setQ] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => { setMobileOpen(false); }, [loc.pathname]);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const submit = (e) => {
    e.preventDefault();
    if (q.trim()) nav(`/catalog?q=${encodeURIComponent(q.trim())}`);
  };

  const link = (to, label, key) => {
    const active = loc.pathname === to || loc.pathname.startsWith(to + "/");
    return (
      <Link data-testid={`nav-link-${key}`} to={to}
        className={`text-sm font-heading transition-colors ${active ? "text-white" : "text-zinc-400 hover:text-white"}`}>
        {label}
      </Link>
    );
  };

  return (
    <header className={`sticky top-0 z-50 border-b ${scrolled ? "glass border-white/10" : "border-transparent bg-transparent"}`}>
      <div className="max-w-[1400px] mx-auto px-5 md:px-8 h-16 flex items-center gap-6">
        <Link to="/" data-testid="nav-brand" className="flex items-center gap-2 shrink-0">
          {settings?.logo_url ? (
            <img src={settings.logo_url} alt="logo" className="h-7 w-auto" />
          ) : (
            <div className="w-7 h-7 rounded-md bg-white text-black flex items-center justify-center font-display font-bold text-[13px]">LP</div>
          )}
          <span className="font-display text-white text-lg tracking-tight">{settings?.logo_text || "LicenzPøl"}</span>
        </Link>

        <nav className="hidden md:flex items-center gap-6 ml-4">
          {link("/catalog", t.nav.catalog, "catalog")}
          {link("/families", t.nav.families, "families")}
          {link("/needs", t.nav.needs, "needs")}
          {link("/bundle", t.nav.bundle, "bundle")}
          {link("/compare", `${t.nav.compare}${compare.length ? ` · ${compare.length}` : ""}`, "compare")}
          {link("/support", t.nav.support, "support")}
        </nav>

        <form onSubmit={submit} className="hidden md:flex flex-1 max-w-md ml-auto items-center gap-2 bg-white/[0.03] border border-white/10 rounded-full px-3 py-2">
          <Search size={16} className="text-zinc-500" />
          <input data-testid="nav-search-input" value={q} onChange={e => setQ(e.target.value)}
            placeholder={t.nav.search}
            className="bg-transparent w-full text-sm text-white placeholder:text-zinc-500 focus:outline-none" />
        </form>

        <div className="flex items-center gap-3 ml-auto md:ml-0">
          <button data-testid="lang-toggle" onClick={() => setLang(lang === "it" ? "en" : "it")}
            className="hidden md:flex items-center gap-1.5 text-xs font-mono uppercase tracking-widest text-zinc-400 hover:text-white transition-colors">
            <Globe size={14} /> {lang}
          </button>
          <Link to="/compare" data-testid="nav-compare-btn" className="hidden md:inline-flex items-center gap-1.5 text-zinc-400 hover:text-white transition-colors">
            <Layers size={18} />
          </Link>
          <button data-testid="nav-cart-btn" onClick={() => setDrawerOpen(true)}
            className="relative inline-flex items-center gap-2 text-zinc-200 hover:text-white transition-colors">
            <ShoppingBag size={18} />
            {count > 0 && <span data-testid="cart-count" className="absolute -top-2 -right-2 min-w-[18px] h-[18px] px-1 rounded-full bg-white text-black text-[10px] font-semibold flex items-center justify-center">{count}</span>}
          </button>
          <button data-testid="nav-mobile-toggle" onClick={() => setMobileOpen(v => !v)} className="md:hidden text-zinc-300">
            {mobileOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="md:hidden border-t border-white/10 bg-black">
          <div className="px-5 py-4 flex flex-col gap-4">
            <form onSubmit={submit} className="flex items-center gap-2 bg-white/[0.03] border border-white/10 rounded-full px-3 py-2">
              <Search size={16} className="text-zinc-500" />
              <input value={q} onChange={e => setQ(e.target.value)} placeholder={t.nav.search}
                className="bg-transparent w-full text-sm text-white placeholder:text-zinc-500 focus:outline-none" />
            </form>
            {link("/catalog", t.nav.catalog, "catalog-m")}
            {link("/families", t.nav.families, "families-m")}
            {link("/needs", t.nav.needs, "needs-m")}
            {link("/bundle", t.nav.bundle, "bundle-m")}
            {link("/compare", `${t.nav.compare} (${compare.length})`, "compare-m")}
            {link("/support", t.nav.support, "support-m")}
            <button data-testid="lang-toggle-m" onClick={() => setLang(lang === "it" ? "en" : "it")}
              className="flex items-center gap-1.5 text-xs font-mono uppercase tracking-widest text-zinc-400">
              <Globe size={14} /> Language · {lang.toUpperCase()}
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
