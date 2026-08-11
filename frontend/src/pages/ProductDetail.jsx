import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { useLang, money } from "../lib/i18n";
import useSEO from "../lib/useSEO";
import { useCart } from "../lib/cart";
import ProductCard from "../components/ProductCard";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "../components/ui/accordion";
import { toast } from "sonner";
import { trackEvent } from "../lib/tracking";
import { productPrice } from "../lib/productPricing";
import { Check, Mail, FileText, KeyRound, Cpu, ChevronRight, Layers } from "lucide-react";

export default function ProductDetail() {
  const { slug } = useParams();
  const { lang, t } = useLang();
  const { addItem, addCompare } = useCart();
  const [product, setProduct] = useState(null);
  const [related, setRelated] = useState([]);
  const [variantId, setVariantId] = useState(null);
  const [added, setAdded] = useState(false);

  useEffect(() => {
    api.product(slug).then(p => {
      setProduct(p);
      setVariantId(p.variants[0].id);
      trackEvent({ event_type: "product_view", product_slug: p.slug });
    });
    api.related(slug).then(setRelated);
    window.scrollTo(0, 0);
  }, [slug]);

  // SEO — computed once product is loaded (hook must run every render)
  const seoData = useMemo(() => {
    if (!product) return {};
    const minPrice = productPrice(product);
    const tagline = lang === "it" ? product.tagline_it : product.tagline_en;
    const desc = lang === "it" ? product.description_it : product.description_en;
    const shortDesc = (desc || tagline || "").slice(0, 160);
    const origin = typeof window !== "undefined" ? window.location.origin : "";
    return {
      title: product.name,
      description: shortDesc || `${product.name} — ${product.brand}. Scheda in revisione; acquisto e consegna non ancora attivi.`,
      keywords: `${product.name}, ${product.brand}, ${product.category}, licenza, ${product.licenseType}`,
      image: product.image_url ? (product.image_url.startsWith("http") ? product.image_url : origin + product.image_url) : undefined,
      type: "product",
      locale: lang === "it" ? "it_IT" : "en_US",
      jsonLd: {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "description": shortDesc,
        "brand": { "@type": "Brand", "name": product.brand },
        "category": product.category,
        "sku": product.sku,
        "image": product.image_url ? [product.image_url.startsWith("http") ? product.image_url : origin + product.image_url] : undefined,
        ...(product.purchasable && minPrice !== null ? { "offers": {
          "@type": "AggregateOffer",
          "priceCurrency": "EUR",
          "lowPrice": minPrice,
          "highPrice": minPrice,
          "offerCount": product.variants.length,
          "availability": "https://schema.org/InStock",
        }} : {}),
      },
    };
  }, [product, lang]);
  useSEO(seoData);

  if (!product) return <div className="max-w-[1400px] mx-auto px-6 py-24 text-center text-zinc-500">Loading...</div>;
  const variant = product.variants.find(v => v.id === variantId) || product.variants[0];
  const editions = [...new Set(product.variants.map(v => v.edition))];
  const durations = [...new Set(product.variants.filter(v => v.edition === variant.edition).map(v => v.duration_months))];
  const devices = [...new Set(product.variants.filter(v => v.edition === variant.edition && v.duration_months === variant.duration_months).map(v => v.devices))];
  const pickVariant = (edition, duration, dev) => {
    const found = product.variants.find(v => v.edition === edition && v.duration_months === duration && v.devices === dev);
    if (found) setVariantId(found.id);
  };

  const doAdd = () => {
    if (!product.purchasable || !Number.isFinite(variant.price_eur)) return;
    addItem(product, variant);
    setAdded(true);
    toast.success(lang === "it" ? "Aggiunto al carrello" : "Added to cart");
    trackEvent({ event_type: "add_to_cart", product_slug: product.slug, value_eur: variant.price_eur });
    setTimeout(() => setAdded(false), 1600);
  };

  const doCompare = () => {
    addCompare(product);
    toast.success(lang === "it" ? "Aggiunto al confronto" : "Added to compare");
  };

  const desc = lang === "it" ? product.description_it : product.description_en;
  const features = lang === "it" ? product.features_it : product.features_en;
  const compat = lang === "it" ? product.compatibility_it : product.compatibility_en;
  const whatYouGet = lang === "it" ? product.whatYouGet_it : product.whatYouGet_en;
  const activation = lang === "it" ? product.activation_it : product.activation_en;

  return (
    <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-12" data-testid="product-page">
      {/* breadcrumb */}
      <nav className="mb-8 flex items-center gap-2 text-xs font-mono text-zinc-500">
        <Link to="/" className="hover:text-white">Home</Link>
        <ChevronRight size={12} />
        <Link to="/catalog" className="hover:text-white">{t.nav.catalog}</Link>
        <ChevronRight size={12} />
        <span className="text-zinc-300">{product.name}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-16">
        {/* VISUAL */}
        <div className="lg:sticky lg:top-24 self-start">
          <div className={`relative rounded-2xl border border-white/10 overflow-hidden aspect-square mesh-${product.colorKey} flex items-center justify-center`}>
            <div className="absolute inset-0 grain" />
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.name}
                className="absolute inset-0 w-full h-full object-contain p-10"
                onError={(e) => { e.currentTarget.style.display = 'none'; }}
              />
            ) : (
              <span className="font-display font-bold text-white/95 tracking-tighter" style={{ fontSize: 'clamp(140px, 22vw, 340px)', lineHeight: 1 }}>{product.mark}</span>
            )}
            <div className="absolute top-4 left-4 flex gap-2">
              {product.platforms.map(p => <span key={p} className="chip bg-black/40 backdrop-blur-sm">{p}</span>)}
            </div>
            <div className="absolute bottom-4 left-4 chip bg-black/40 backdrop-blur-sm"><KeyRound size={12} /> {product.licenseType}</div>
          </div>
        </div>

        {/* DETAILS */}
        <div>
          <p className="label-eyebrow mb-2">{product.brand}</p>
          <h1 data-testid="product-title" className="font-display tracking-tighter text-white text-4xl md:text-5xl leading-[1.05]">{product.name}</h1>
          <p className="text-zinc-400 text-lg mt-4">{lang === "it" ? product.tagline_it : product.tagline_en}</p>
          <p className="text-zinc-500 mt-4 leading-relaxed">{desc}</p>

          <div className="mt-8 p-6 rounded-xl border border-white/10 bg-[#0B0B0D]">
            <p className="label-eyebrow mb-4">{t.product.choose}</p>

            {editions.length > 1 && (
              <div className="mb-5">
                <p className="text-xs text-zinc-500 mb-2 font-mono uppercase tracking-widest">{t.product.variantEdition}</p>
                <div className="flex flex-wrap gap-2">
                  {editions.map(e => {
                    const active = variant.edition === e;
                    return (
                      <button key={e} data-testid={`variant-edition-${e}`} onClick={() => pickVariant(e, product.variants.find(v => v.edition === e).duration_months, product.variants.find(v => v.edition === e).devices)}
                        className={`px-4 py-2 rounded-full text-sm border transition-all ${active ? "border-white bg-white text-black" : "border-white/15 text-zinc-300 hover:border-white/40"}`}>
                        {e}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {durations.length > 1 && (
              <div className="mb-5">
                <p className="text-xs text-zinc-500 mb-2 font-mono uppercase tracking-widest">{t.product.variantDuration}</p>
                <div className="flex flex-wrap gap-2">
                  {durations.map(d => {
                    const active = variant.duration_months === d;
                    const label = d === 0 ? t.product.perpetual : `${d} ${t.product.months}`;
                    return (
                      <button key={d} data-testid={`variant-duration-${d}`} onClick={() => pickVariant(variant.edition, d, devices[0])}
                        className={`px-4 py-2 rounded-full text-sm border transition-all ${active ? "border-white bg-white text-black" : "border-white/15 text-zinc-300 hover:border-white/40"}`}>
                        {label}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {devices.length > 1 && (
              <div className="mb-6">
                <p className="text-xs text-zinc-500 mb-2 font-mono uppercase tracking-widest">{t.product.variantDevices}</p>
                <div className="flex flex-wrap gap-2">
                  {devices.map(d => {
                    const active = variant.devices === d;
                    return (
                      <button key={d} data-testid={`variant-devices-${d}`} onClick={() => pickVariant(variant.edition, variant.duration_months, d)}
                        className={`px-4 py-2 rounded-full text-sm border transition-all ${active ? "border-white bg-white text-black" : "border-white/15 text-zinc-300 hover:border-white/40"}`}>
                        {d} {d === 1 ? t.product.device : t.product.devices}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="flex items-end justify-between mb-5 border-t border-white/5 pt-5">
              <div>
                <p className="text-[10px] font-mono uppercase tracking-widest text-zinc-500">Price</p>
                <div className="flex items-baseline gap-3">
                  <p data-testid="product-price" className="font-display text-white text-4xl">{Number.isFinite(variant.price_eur) ? money(variant.price_eur) : (lang === "it" ? "In verifica" : "Under review")}</p>
                  {variant.list_price_eur && variant.list_price_eur > variant.price_eur && (
                    <p className="text-sm font-mono text-zinc-500 line-through">{money(variant.list_price_eur)}</p>
                  )}
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <button data-testid="add-to-cart-button" onClick={doAdd} disabled={!product.purchasable}
                className="pill-btn bg-white text-black hover:bg-zinc-200 flex-1 disabled:bg-zinc-700 disabled:text-zinc-300 disabled:cursor-not-allowed">
                {!product.purchasable ? (lang === "it" ? "Non disponibile — dati in verifica" : "Unavailable — data under review") : added ? (<><Check size={16}/> {t.product.added}</>) : t.product.addToCart}
              </button>
              <button data-testid="add-to-compare-button" onClick={doCompare}
                className="pill-btn border border-white/20 text-white hover:bg-white/5">
                <Layers size={16}/> {t.product.compareAdd}
              </button>
            </div>

            <div className="mt-5 grid grid-cols-3 gap-2 text-[11px] text-zinc-500">
              <span className="inline-flex items-center gap-1.5"><Mail size={12}/>{t.product.instantDelivery}</span>
              <span className="inline-flex items-center gap-1.5"><FileText size={12}/>{t.product.invoice}</span>
              <span className="inline-flex items-center gap-1.5"><KeyRound size={12}/>{t.product.support}</span>
            </div>
          </div>

          {/* Details sections */}
          <div className="mt-12 space-y-10">
            <section>
              <p className="label-eyebrow mb-3">{t.product.whatYouGet}</p>
              <ul className="space-y-2">
                {whatYouGet.map((it, i) => (
                  <li key={i} className="flex items-start gap-2 text-zinc-300"><Check size={16} className="mt-1 text-green-400" /><span>{it}</span></li>
                ))}
              </ul>
            </section>
            <section>
              <p className="label-eyebrow mb-3">Features</p>
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {features.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-zinc-300"><Check size={16} className="mt-1 text-zinc-500" /><span>{f}</span></li>
                ))}
              </ul>
            </section>
            <section>
              <p className="label-eyebrow mb-3">{t.product.compat}</p>
              <div className="flex items-start gap-3 text-zinc-400">
                <Cpu size={18} className="mt-0.5 text-zinc-500" />
                <p>{compat}</p>
              </div>
            </section>
            <section>
              <p className="label-eyebrow mb-3">{t.product.activation}</p>
              <ol className="space-y-3">
                {activation.map((a, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full border border-white/15 text-xs font-mono flex items-center justify-center shrink-0">{i + 1}</span>
                    <span className="text-zinc-300">{a}</span>
                  </li>
                ))}
              </ol>
            </section>
            <section>
              <p className="label-eyebrow mb-3">FAQ</p>
              <Accordion type="single" collapsible>
                {product.faq.map((f, i) => (
                  <AccordionItem key={i} value={`f-${i}`} className="border-b border-white/10">
                    <AccordionTrigger className="text-white text-left font-heading hover:no-underline">{lang === "it" ? f.q_it : f.q_en}</AccordionTrigger>
                    <AccordionContent className="text-zinc-400 leading-relaxed">{lang === "it" ? f.a_it : f.a_en}</AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </section>
          </div>
        </div>
      </div>

      {related.length > 0 && (
        <section className="mt-24">
          <p className="label-eyebrow mb-3">Related</p>
          <h2 className="font-display text-3xl md:text-4xl tracking-tight mb-8">{t.product.relatedTitle}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {related.map(p => <ProductCard key={p.slug} product={p} />)}
          </div>
        </section>
      )}
    </div>
  );
}
