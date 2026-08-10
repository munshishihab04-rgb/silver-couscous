import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { useLang } from "../lib/i18n";
import { api } from "../lib/api";
import axios from "axios";
import { Circle, Info } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function useCmsPage(slug) {
  const [page, setPage] = useState(null);
  useEffect(() => {
    axios.get(`${API}/pages/${slug}`).then(r => setPage(r.data)).catch(() => setPage(null));
  }, [slug]);
  return page;
}

function CmsRender({ slug, fallbackTitle, children }) {
  const { lang } = useLang();
  const page = useCmsPage(slug);
  if (!page) return children;
  const content = lang === "it" ? page.content_it : page.content_en;
  const title = lang === "it" ? page.title_it : page.title_en;
  return (
    <div>
      <p className="label-eyebrow mb-2">CMS</p>
      <h1 className="font-display text-4xl md:text-5xl tracking-tight">{title || fallbackTitle}</h1>
      <div className="mt-8 whitespace-pre-wrap text-zinc-400 leading-relaxed font-mono text-sm">{content}</div>
    </div>
  );
}

export function Transparency() {
  const { lang } = useLang();
  const it = lang === "it";
  return (
    <div className="max-w-[900px] mx-auto px-6 py-16" data-testid="transparency-page">
      <p className="label-eyebrow mb-2">Trust</p>
      <h1 className="font-display text-4xl md:text-5xl tracking-tight">{it ? "Trasparenza" : "Transparency"}</h1>
      <div className="space-y-6 mt-8 text-zinc-400 leading-relaxed">
        <p>{it
          ? "LicenzPol è un progetto in fase di avvio. Vogliamo essere onesti su cosa è già pronto e cosa non lo è ancora."
          : "LicenzPol is an early-stage project. We want to be honest about what is ready and what isn't."}</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { l: "Demo", c: "orange", t: it ? "Pagamenti" : "Payments", d: it ? "Il checkout è in modalità demo: nessun pagamento reale viene elaborato." : "Checkout is in demo mode: no real payments are processed." },
            { l: "Demo", c: "orange", t: it ? "Consegna della chiave" : "Key delivery", d: it ? "In produzione, le chiavi verrebbero consegnate via email dopo l'ordine." : "In production, keys would be emailed after the order." },
            { l: "Live", c: "green", t: it ? "Catalogo" : "Catalog", d: it ? "Il catalogo è navigabile con prezzi e varianti plausibili." : "The catalog is navigable with plausible prices and variants." },
            { l: "Live", c: "green", t: it ? "Confronto e filtri" : "Compare & filters", d: it ? "Puoi confrontare fino a 3 prodotti e filtrare per bisogno, brand e piattaforma." : "You can compare up to 3 products and filter by need, brand and platform." },
          ].map((x, i) => (
            <div key={i} className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
              <div className="flex items-center gap-2 mb-2">
                <Circle size={7} className={x.c === "green" ? "fill-green-400 text-green-400" : "fill-orange-400 text-orange-400"} />
                <span className="label-eyebrow">{x.l}</span>
              </div>
              <p className="font-heading text-white">{x.t}</p>
              <p className="text-sm text-zinc-500 mt-1">{x.d}</p>
            </div>
          ))}
        </div>
        <p className="text-sm">{it
          ? "Non inventiamo recensioni, certificazioni, partnership o disponibilità. Se qualcosa non è verificato, non compare sul sito."
          : "We do not fabricate reviews, certifications, partnerships or availability. If something isn't verified, it isn't on the site."}</p>
        <Link to="/support" className="pill-btn border border-white/20 text-white hover:bg-white/5 inline-flex">
          <Info size={14} /> {it ? "Hai domande?" : "Any questions?"}
        </Link>
      </div>
    </div>
  );
}

export function Legal({ kind }) {
  const { lang } = useLang();
  const it = lang === "it";
  const title = { privacy: it ? "Privacy" : "Privacy", terms: it ? "Termini" : "Terms", cookies: "Cookie" }[kind];
  return (
    <div className="max-w-[900px] mx-auto px-6 py-16" data-testid={`legal-${kind}`}>
      <CmsRender slug={kind} fallbackTitle={title}>
        <p className="label-eyebrow mb-2">Legal</p>
        <h1 className="font-display text-4xl md:text-5xl tracking-tight">{title}</h1>
        <div className="mt-8 text-zinc-400 space-y-4 leading-relaxed">
          <p>{it
            ? "Questa è una pagina segnaposto per il prototipo. Amministrala dal pannello admin."
            : "Placeholder page. Manage from the admin panel."}</p>
        </div>
      </CmsRender>
    </div>
  );
}

export function Needs() {
  const { lang, t } = useLang();
  return (
    <div className="max-w-[1200px] mx-auto px-6 md:px-10 py-16" data-testid="needs-page">
      <p className="label-eyebrow mb-2">Discover</p>
      <h1 className="font-display text-4xl md:text-6xl tracking-tight">{t.needs.title}</h1>
      <p className="text-zinc-400 mt-4 max-w-lg">{t.needs.sub}</p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-10">
        {[
          { k: "work", c: "work" }, { k: "protect", c: "protect" }, { k: "design", c: "design" },
          { k: "create", c: "create" }, { k: "manage", c: "manage" }, { k: "update", c: "work" },
        ].map(n => (
          <Link key={n.k} data-testid={`needs-tile-${n.k}`} to={`/catalog?need=${n.k}`}
            className={`card-hover relative rounded-xl border border-white/10 mesh-${n.c} p-8 md:p-10 min-h-[220px] flex flex-col justify-between overflow-hidden`}>
            <div className="absolute inset-0 grain" />
            <span className="relative label-eyebrow">{n.k}</span>
            <div className="relative">
              <h3 className="font-display text-white text-2xl md:text-3xl tracking-tight">
                {lang === "it"
                  ? { work: "Lavorare", protect: "Proteggere", design: "Progettare", create: "Creare", manage: "Gestire", update: "Aggiornare il PC" }[n.k]
                  : { work: "Work", protect: "Protect", design: "Design", create: "Create", manage: "Manage", update: "Update PC" }[n.k]}
              </h3>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
