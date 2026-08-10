import { Link } from "react-router-dom";
import { useLang, money } from "../lib/i18n";
import { Monitor, Apple, Cpu, Check } from "lucide-react";

const platformIcon = (p) => {
  if (p === "Windows") return <Monitor size={12} />;
  if (p === "macOS") return <Apple size={12} />;
  return <Cpu size={12} />;
};

export default function ProductCard({ product, testid }) {
  const { lang, t } = useLang();
  const min = Math.min(...product.variants.map(v => v.price_eur));
  const max = Math.max(...product.variants.map(v => v.list_price_eur ?? v.price_eur));
  const hasDiscount = max > min;
  const tagline = lang === "it" ? product.tagline_it : product.tagline_en;

  return (
    <Link
      data-testid={testid || `product-card-${product.slug}`}
      to={`/product/${product.slug}`}
      className="card-hover group relative flex flex-col rounded-xl border border-white/10 bg-[#0B0B0D] overflow-hidden"
    >
      <div className={`relative aspect-[4/3] overflow-hidden mesh-${product.colorKey}`}>
        <div className="absolute inset-0 grain" />
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            loading="lazy"
            className="absolute inset-0 w-full h-full object-contain p-6"
            onError={(e) => { e.currentTarget.style.display = 'none'; }}
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="font-display font-bold text-white/95 tracking-tight" style={{ fontSize: 'clamp(50px, 7vw, 120px)', lineHeight: 1 }}>
              {product.mark}
            </span>
          </div>
        )}
        <div className="absolute top-3 left-3 flex gap-1.5">
          {product.platforms.slice(0, 3).map(p => (
            <span key={p} className="chip !py-1 !px-2 !text-[10px] bg-black/40 backdrop-blur-sm">{platformIcon(p)}{p}</span>
          ))}
        </div>
        {hasDiscount && (
          <div className="absolute top-3 right-3 text-[10px] font-mono uppercase tracking-widest px-2 py-1 rounded-full bg-white text-black">
            -{Math.round((1 - min / max) * 100)}%
          </div>
        )}
      </div>
      <div className="p-5 flex flex-col gap-3 flex-1">
        <div className="flex items-center gap-2">
          <span className="label-eyebrow">{product.brand}</span>
          <span className="text-zinc-700">·</span>
          <span className="text-[11px] text-zinc-500 uppercase tracking-widest font-mono">{product.licenseType}</span>
        </div>
        <h3 className="font-display text-white text-lg leading-tight">{product.name}</h3>
        <p className="text-sm text-zinc-500 leading-relaxed line-clamp-2">{tagline}</p>
        <div className="mt-auto pt-3 flex items-end justify-between border-t border-white/5">
          <div>
            <p className="text-[10px] uppercase tracking-widest font-mono text-zinc-600">{t.compare.cols.startingAt}</p>
            <div className="flex items-baseline gap-2">
              <p className="font-display text-white text-2xl">{money(min)}</p>
              {hasDiscount && <p className="text-xs font-mono text-zinc-600 line-through">{money(max)}</p>}
            </div>
          </div>
          <div className="text-zinc-500 group-hover:text-white transition-colors">
            <Check size={16} />
          </div>
        </div>
      </div>
    </Link>
  );
}
