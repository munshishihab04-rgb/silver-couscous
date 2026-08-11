import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useLang } from "../lib/i18n";
import useSEO from "../lib/useSEO";
import ProductCard from "../components/ProductCard";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../components/ui/accordion";
import {
  Briefcase, ShieldCheck, Palette, Sparkles, Building2, RefreshCw,
  ArrowRight, ArrowUpRight, Zap, Mail, FileText, KeyRound, Rocket,
  Lock, Circle, ChevronRight, Layers
} from "lucide-react";

const needIcon = { briefcase: Briefcase, "shield-check": ShieldCheck, palette: Palette, sparkles: Sparkles, "building-2": Building2, "refresh-cw": RefreshCw };

export default function Home() {
  const { lang, t } = useLang();
  const [needs, setNeeds] = useState([]);
  const [cats, setCats] = useState([]);
  const [families, setFamilies] = useState([]);
  const [curated, setCurated] = useState([]);

  useSEO({
    title: lang === "it"
      ? "LicenzPol — ambiente di pre-lancio"
      : "LicenzPol — pre-launch environment",
    description: lang === "it"
      ? "Catalogo, prezzi, disponibilità e checkout sono in verifica. Nessun pagamento reale è attivo."
      : "Catalogue, prices, availability and checkout are under review. No real payment is active.",
    keywords: "licenze software, microsoft office, windows, adobe, autodesk, antivirus, chiavi digitali, licenzpol",
    type: "website",
    locale: lang === "it" ? "it_IT" : "en_US",
    jsonLd: {
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": "LicenzPøl",
      "url": typeof window !== "undefined" ? window.location.origin : "",
      "potentialAction": {
        "@type": "SearchAction",
        "target": typeof window !== "undefined" ? `${window.location.origin}/catalog?q={search_term_string}` : "",
        "query-input": "required name=search_term_string",
      },
    },
  });

  useEffect(() => {
    Promise.all([api.needs(), api.categories(), api.families(), api.products({ limit: 8 })])
      .then(([n, c, f, p]) => { setNeeds(n); setCats(c); setFamilies(f); setCurated(p.items); });
  }, []);

  return (
    <div className="text-white" data-testid="home-page">
      {/* HERO */}
      <section className="relative overflow-hidden border-b border-white/10">
        <div className="absolute inset-0 dashed-grid opacity-40" />
        <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full bg-blue-500/10 blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-[600px] h-[600px] rounded-full bg-orange-500/10 blur-3xl" />
        <div className="absolute inset-0 grain" />

        <div className="relative max-w-[1400px] mx-auto px-6 md:px-10 pt-20 md:pt-28 pb-20 md:pb-32">
          <div className="max-w-4xl">
            <div className="inline-flex items-center gap-2 chip mb-8 fade-up">
              <Circle size={6} className="fill-green-400 text-green-400" /> {t.hero.eyebrow}
            </div>
            <h1 className="font-display font-medium tracking-tighter text-white fade-up" style={{ fontSize: 'clamp(48px, 9vw, 140px)', lineHeight: 0.95 }}>
              {t.hero.title1}<br />
              <span className="text-zinc-500">{t.hero.title2}</span>
            </h1>
            <p className="mt-8 text-zinc-400 text-lg md:text-xl max-w-2xl leading-relaxed fade-up">{t.hero.sub}</p>
            <div className="mt-10 flex flex-wrap gap-3 fade-up">
              <Link data-testid="hero-cta-catalog" to="/catalog" className="pill-btn bg-white text-black hover:bg-zinc-200">
                {t.hero.ctaCatalog} <ArrowRight size={16} />
              </Link>
              <Link data-testid="hero-cta-needs" to="/needs" className="pill-btn border border-white/20 text-white hover:bg-white/5">
                {t.hero.ctaNeeds}
              </Link>
            </div>
            <div className="mt-10 flex flex-wrap gap-x-6 gap-y-2 text-xs font-mono text-zinc-500">
              <span className="inline-flex items-center gap-2"><Mail size={12}/> {t.hero.badge1}</span>
              <span className="inline-flex items-center gap-2"><FileText size={12}/> {t.hero.badge2}</span>
              <span className="inline-flex items-center gap-2"><KeyRound size={12}/> {t.hero.badge3}</span>
            </div>
          </div>
        </div>
      </section>

      {/* NEEDS */}
      <section className="border-b border-white/10">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-20 md:py-28">
          <div className="flex items-end justify-between flex-wrap gap-4 mb-12">
            <div>
              <p className="label-eyebrow mb-3">01 / {t.hero.eyebrow}</p>
              <h2 className="font-display text-4xl md:text-5xl tracking-tight max-w-2xl">{t.needs.title}</h2>
            </div>
            <p className="text-zinc-500 max-w-md text-sm">{t.needs.sub}</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {needs.map((n, i) => {
              const Icon = needIcon[n.icon] || Briefcase;
              return (
                <Link key={n.key} data-testid={`need-tile-${n.key}`} to={`/catalog?need=${n.key}`}
                  className={`card-hover relative overflow-hidden rounded-xl border border-white/10 mesh-${n.color} p-6 md:p-8 min-h-[180px] flex flex-col justify-between`}>
                  <div className="absolute inset-0 grain" />
                  <div className="relative z-10 flex items-center justify-between">
                    <Icon size={22} className="text-white/80" />
                    <span className="text-[10px] font-mono uppercase tracking-widest text-white/50">0{i + 1}</span>
                  </div>
                  <div className="relative z-10">
                    <h3 className="font-display text-white text-2xl md:text-3xl tracking-tight">{lang === "it" ? n.title_it : n.title_en}</h3>
                    <p className="text-sm text-white/70 mt-2">{lang === "it" ? n.desc_it : n.desc_en}</p>
                    <span className="inline-flex items-center gap-1 mt-4 text-xs text-white/80">
                      <ArrowUpRight size={14} />
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* CATEGORIES */}
      <section className="border-b border-white/10">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-20">
          <p className="label-eyebrow mb-3">02 / Catalog</p>
          <h2 className="font-display text-4xl md:text-5xl tracking-tight mb-12">{t.categoriesTitle}</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {cats.map(c => (
              <Link key={c.key} data-testid={`cat-tile-${c.key}`} to={`/catalog?category=${c.key}`}
                className="card-hover group flex items-center justify-between rounded-xl border border-white/10 bg-[#0B0B0D] p-5 hover:bg-[#111114]">
                <div>
                  <p className="label-eyebrow mb-1">{c.key}</p>
                  <p className="font-heading text-white text-lg">{lang === "it" ? c.name_it : c.name_en}</p>
                </div>
                <ChevronRight size={18} className="text-zinc-500 group-hover:text-white transition-colors" />
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* FAMILIES */}
      <section className="border-b border-white/10">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-20">
          <div className="flex items-end justify-between flex-wrap gap-4 mb-10">
            <div>
              <p className="label-eyebrow mb-3">02b / Families</p>
              <h2 className="font-display text-4xl md:text-5xl tracking-tight">
                {lang === "it" ? "Le famiglie principali" : "Signature families"}
              </h2>
              <p className="text-zinc-500 mt-3 max-w-xl text-sm">
                {lang === "it"
                  ? "Da Windows a Adobe, ogni grande brand ha la sua pagina dedicata."
                  : "From Windows to Adobe, every major brand has a dedicated page."}
              </p>
            </div>
            <Link to="/families" data-testid="home-families-all" className="pill-btn border border-white/20 text-white hover:bg-white/5">
              {lang === "it" ? "Tutte le famiglie" : "All families"} <ArrowUpRight size={14} />
            </Link>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {families.map(f => (
              <Link key={f.slug} data-testid={`home-family-${f.slug}`} to={`/family/${f.slug}`}
                className={`card-hover relative overflow-hidden rounded-xl border border-white/10 mesh-${f.colorKey} p-6 min-h-[180px] flex flex-col justify-between`}>
                <div className="absolute inset-0 grain" />
                <div className="relative flex items-center justify-between">
                  <Layers size={18} className="text-white/80" />
                  <span className="text-[10px] font-mono uppercase tracking-widest text-white/60">{f.product_count}</span>
                </div>
                <div className="relative">
                  <h3 className="font-display text-white text-xl md:text-2xl tracking-tight">{lang === "it" ? f.name_it : f.name_en}</h3>
                  <p className="text-xs text-white/70 mt-1 line-clamp-2">{lang === "it" ? f.tagline_it : f.tagline_en}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CURATED */}
      <section className="border-b border-white/10">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-20">
          <div className="flex items-end justify-between flex-wrap gap-4 mb-12">
            <div>
              <p className="label-eyebrow mb-3">03 / Selection</p>
              <h2 className="font-display text-4xl md:text-5xl tracking-tight">{t.curated.title}</h2>
              <p className="text-zinc-500 mt-3 max-w-lg text-sm">{t.curated.sub}</p>
            </div>
            <Link to="/catalog" data-testid="curated-see-all" className="pill-btn border border-white/20 text-white hover:bg-white/5">
              {t.hero.ctaCatalog} <ArrowUpRight size={14} />
            </Link>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {curated.slice(0, 8).map(p => <ProductCard key={p.slug} product={p} />)}
          </div>
        </div>
      </section>

      {/* BUNDLE PROMO */}
      <section className="border-b border-white/10">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-20">
          <Link to="/bundle" data-testid="home-bundle-cta"
            className="group relative block rounded-2xl border border-white/10 overflow-hidden card-hover">
            <div className="absolute inset-0 mesh-work opacity-90" />
            <div className="absolute inset-0 grain" />
            <div className="absolute -right-32 -bottom-40 w-[520px] h-[520px] rounded-full bg-blue-500/20 blur-3xl" />
            <div className="relative p-8 md:p-14 grid grid-cols-1 md:grid-cols-2 gap-8 items-end">
              <div>
                <p className="label-eyebrow mb-3">{t.bundle.eyebrow}</p>
                <h2 className="font-display tracking-tighter text-white" style={{ fontSize: 'clamp(38px, 6vw, 84px)', lineHeight: 0.95 }}>
                  {t.bundle.title} <span className="text-white/60">{t.bundle.title2}</span>
                </h2>
                <p className="text-white/70 mt-4 max-w-md">{t.bundle.sub}</p>
              </div>
              <div className="flex flex-col gap-3 items-start md:items-end">
                <div className="flex flex-wrap gap-2 md:justify-end">
                  {t.bundle.tiers.map((tier, i) => (
                    <span key={i} className="chip bg-black/40 backdrop-blur-sm">{tier.n}+ · {tier.d}</span>
                  ))}
                </div>
                <span className="pill-btn bg-white text-black group-hover:bg-zinc-200">
                  {t.bundle.cta} <ArrowRight size={16} />
                </span>
              </div>
            </div>
          </Link>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="border-b border-white/10">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-20">
          <p className="label-eyebrow mb-3">04 / How</p>
          <h2 className="font-display text-4xl md:text-5xl tracking-tight mb-12 max-w-2xl">{t.how.title}</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {t.how.steps.map((s, i) => (
              <div key={i} className="rounded-xl border border-white/10 bg-[#0B0B0D] p-6 min-h-[200px] flex flex-col justify-between">
                <span className="font-mono text-xs text-zinc-500">0{i + 1}</span>
                <div>
                  <h3 className="font-display text-white text-xl mb-2">{s.t}</h3>
                  <p className="text-sm text-zinc-500 leading-relaxed">{s.d}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* WHY LICENZPOL */}
      <section className="border-b border-white/10">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-20">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
            <div>
              <p className="label-eyebrow mb-3">05 / Why</p>
              <h2 className="font-display text-4xl md:text-5xl tracking-tight max-w-md">{t.why.title}</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-8">
              {t.why.items.map((it, i) => (
                <div key={i} className="border-t border-white/10 pt-6">
                  <div className="flex items-center gap-2 text-zinc-500 mb-3">
                    {[Zap, Lock, Rocket, KeyRound][i % 4] && (() => { const I = [Zap, Lock, Rocket, KeyRound][i % 4]; return <I size={16} />; })()}
                    <span className="text-xs font-mono uppercase tracking-widest">0{i + 1}</span>
                  </div>
                  <h3 className="font-display text-white text-xl mb-2">{it.t}</h3>
                  <p className="text-sm text-zinc-500 leading-relaxed">{it.d}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* TRANSPARENCY */}
      <section className="border-b border-white/10">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-20">
          <div className="rounded-2xl border border-white/10 bg-[#0B0B0D] p-8 md:p-14 relative overflow-hidden">
            <div className="absolute inset-0 grain" />
            <div className="absolute -top-20 -right-20 w-80 h-80 rounded-full bg-white/[0.02] blur-3xl" />
            <div className="relative max-w-3xl">
              <p className="label-eyebrow mb-3">06 / Trust</p>
              <h2 className="font-display text-3xl md:text-4xl tracking-tight mb-4">{t.transparency.title}</h2>
              <p className="text-zinc-400 leading-relaxed">{t.transparency.body}</p>
              <div className="mt-6 flex gap-3 flex-wrap">
                <span className="chip"><Circle size={6} className="fill-orange-400 text-orange-400" /> Demo mode</span>
                <Link to="/transparency" className="pill-btn border border-white/20 text-white text-sm hover:bg-white/5">
                  {t.footer.transparency} <ArrowUpRight size={14} />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="border-b border-white/10">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-20 grid grid-cols-1 lg:grid-cols-2 gap-16">
          <div>
            <p className="label-eyebrow mb-3">07 / FAQ</p>
            <h2 className="font-display text-4xl md:text-5xl tracking-tight">{t.faqTitle}</h2>
          </div>
          <Accordion type="single" collapsible className="w-full">
            {t.faq.map((f, i) => (
              <AccordionItem key={i} value={`item-${i}`} className="border-b border-white/10">
                <AccordionTrigger data-testid={`faq-${i}`} className="font-heading text-white text-left text-lg hover:no-underline">{f.q}</AccordionTrigger>
                <AccordionContent className="text-zinc-400 leading-relaxed">{f.a}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      {/* FINAL CTA */}
      <section>
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-24 text-center">
          <p className="label-eyebrow mb-4">Start</p>
          <h2 className="font-display tracking-tighter text-white" style={{ fontSize: 'clamp(40px, 7vw, 100px)', lineHeight: 1 }}>
            {t.finalCta.title}
          </h2>
          <p className="text-zinc-400 mt-4 max-w-md mx-auto">{t.finalCta.sub}</p>
          <Link data-testid="final-cta" to="/catalog" className="pill-btn bg-white text-black hover:bg-zinc-200 mt-8 inline-flex">
            {t.finalCta.cta} <ArrowRight size={16} />
          </Link>
        </div>
      </section>
    </div>
  );
}
