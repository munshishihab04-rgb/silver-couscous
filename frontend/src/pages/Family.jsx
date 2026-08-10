import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { useLang } from "../lib/i18n";
import ProductCard from "../components/ProductCard";
import { ChevronRight, ArrowRight, Layers } from "lucide-react";

export default function Family() {
  const { slug } = useParams();
  const { lang, t } = useLang();
  const [family, setFamily] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true); setFamily(null);
    window.scrollTo(0, 0);
    api.family(slug).then(setFamily).finally(() => setLoading(false));
  }, [slug]);

  if (loading || !family) {
    return <div className="max-w-[1400px] mx-auto px-6 py-24 text-center text-zinc-500">Loading...</div>;
  }

  const name = lang === "it" ? family.name_it : family.name_en;
  const tagline = lang === "it" ? family.tagline_it : family.tagline_en;
  const story = lang === "it" ? family.story_it : family.story_en;

  return (
    <div className="text-white" data-testid={`family-${slug}`}>
      {/* HERO */}
      <section className="relative overflow-hidden border-b border-white/10">
        <div className={`absolute inset-0 mesh-${family.colorKey}`} />
        <div className="absolute inset-0 grain" />
        <div className="absolute -top-40 -right-40 w-[600px] h-[600px] rounded-full bg-white/[0.04] blur-3xl" />
        <div className="relative max-w-[1400px] mx-auto px-6 md:px-10 pt-14 md:pt-20 pb-16">
          <nav className="mb-8 flex items-center gap-2 text-xs font-mono text-white/60">
            <Link to="/" className="hover:text-white transition-colors">Home</Link>
            <ChevronRight size={12} />
            <Link to="/families" className="hover:text-white transition-colors">
              {lang === "it" ? "Famiglie" : "Families"}
            </Link>
            <ChevronRight size={12} />
            <span className="text-white">{name}</span>
          </nav>

          <div className="grid grid-cols-1 lg:grid-cols-[1.4fr_1fr] gap-10 items-end">
            <div>
              <p className="label-eyebrow mb-4" style={{ color: "rgba(255,255,255,0.6)" }}>
                {family.product_count} {lang === "it" ? "prodotti" : "products"}
              </p>
              <h1 className="font-display font-medium tracking-tighter text-white"
                style={{ fontSize: 'clamp(48px, 9vw, 130px)', lineHeight: 0.95 }}>
                {name}
              </h1>
              <p className="mt-6 text-white/85 text-xl md:text-2xl font-heading max-w-2xl">{tagline}</p>
              <p className="mt-4 text-white/70 leading-relaxed max-w-2xl">{story}</p>

              <div className="mt-8 flex flex-wrap gap-3">
                <a href="#groups" data-testid="family-explore-cta"
                  className="pill-btn bg-white text-black hover:bg-zinc-200">
                  {lang === "it" ? "Esplora la famiglia" : "Explore the family"} <ArrowRight size={16} />
                </a>
                <Link to={`/catalog?brand=${encodeURIComponent(family.brand)}`}
                  className="pill-btn border border-white/25 text-white hover:bg-white/10">
                  {lang === "it" ? "Vedi nel catalogo" : "See in catalog"}
                </Link>
              </div>
            </div>

            {/* Featured products in-hero */}
            <div className="hidden lg:grid grid-cols-2 gap-3">
              {family.featured.slice(0, 4).map(p => (
                <Link key={p.slug} to={`/product/${p.slug}`}
                  className="card-hover group rounded-xl border border-white/15 bg-black/40 backdrop-blur p-4 flex flex-col">
                  <div className={`aspect-[4/3] rounded-md mesh-${p.colorKey} relative overflow-hidden flex items-center justify-center mb-3`}>
                    {p.image_url ? (
                      <img src={p.image_url} alt={p.name}
                        className="absolute inset-0 w-full h-full object-contain p-4"
                        onError={(e) => { e.currentTarget.style.display = 'none'; }} />
                    ) : (
                      <span className="font-display font-bold text-white text-5xl">{p.mark}</span>
                    )}
                  </div>
                  <p className="label-eyebrow text-white/70">{p.brand}</p>
                  <p className="text-white text-sm leading-tight line-clamp-2">{p.name}</p>
                  <p className="mt-2 font-mono text-sm text-white">
                    {new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(p.variants[0].price_eur)}
                  </p>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* GROUPS */}
      <section id="groups" className="max-w-[1400px] mx-auto px-6 md:px-10 py-16 space-y-16">
        {family.groups.map(g => (
          <div key={g.key} data-testid={`family-group-${g.key}`}>
            <div className="flex items-end justify-between flex-wrap gap-4 mb-6 border-b border-white/10 pb-4">
              <div>
                <p className="label-eyebrow mb-2">{g.items.length} {lang === "it" ? "prodotti" : "products"}</p>
                <h2 className="font-display text-3xl md:text-4xl tracking-tight">{lang === "it" ? g.label_it : g.label_en}</h2>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {g.items.map(p => <ProductCard key={p.slug} product={p} />)}
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}

export function FamiliesIndex() {
  const { lang } = useLang();
  const [families, setFamilies] = useState([]);
  useEffect(() => { api.families().then(setFamilies); }, []);
  return (
    <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-16" data-testid="families-index">
      <p className="label-eyebrow mb-3">Discover</p>
      <h1 className="font-display text-4xl md:text-6xl tracking-tighter">
        {lang === "it" ? "Le famiglie di software" : "Software families"}
      </h1>
      <p className="text-zinc-400 mt-4 max-w-xl">
        {lang === "it"
          ? "Le grandi collezioni, ciascuna con la propria storia."
          : "Big collections, each with its own story."}
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-10">
        {families.map(f => (
          <Link key={f.slug} data-testid={`family-tile-${f.slug}`} to={`/family/${f.slug}`}
            className={`card-hover relative rounded-xl border border-white/10 mesh-${f.colorKey} p-8 md:p-10 min-h-[220px] flex flex-col justify-between overflow-hidden`}>
            <div className="absolute inset-0 grain" />
            <div className="relative flex items-start justify-between">
              <Layers size={22} className="text-white/80" />
              <span className="chip bg-black/40 backdrop-blur-sm">{f.product_count} {lang === "it" ? "prodotti" : "products"}</span>
            </div>
            <div className="relative">
              <h3 className="font-display text-white text-3xl md:text-4xl tracking-tight">{lang === "it" ? f.name_it : f.name_en}</h3>
              <p className="text-white/70 mt-2 text-sm max-w-md">{lang === "it" ? f.tagline_it : f.tagline_en}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
