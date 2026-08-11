import { useEffect, useMemo, useState } from "react";
import { adminApi, useAdminAuth } from "./auth.jsx";
import { toast } from "sonner";
import {
  ShieldCheck, ShieldAlert, KeyRound, Filter, Search, CheckCircle2,
  XCircle, Upload, TrendingUp, PackageCheck, Info,
} from "lucide-react";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api/admin/merchant`;

function useMerchant(token) {
  const client = useMemo(() => axios.create({
    baseURL: API,
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  }), [token]);
  return {
    status: () => client.get("/status").then(r => r.data),
    queue: (params) => client.get("/queue", { params }).then(r => r.data),
    patch: (slug, body) => client.patch(`/products/${slug}`, body).then(r => r.data),
    bulkApprove: (body) => client.post("/bulk-approve", body).then(r => r.data),
    importLicenses: (body) => client.post("/licenses/import", body).then(r => r.data),
    licenseStatus: (sku) => client.get(`/licenses/${sku}`).then(r => r.data),
  };
}

function RiskBadge({ risk }) {
  const score = risk?.score ?? 0;
  const cls = score <= 20 ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
    : score <= 40 ? "bg-yellow-500/10 text-yellow-300 border-yellow-500/30"
    : score <= 60 ? "bg-orange-500/10 text-orange-300 border-orange-500/30"
    : "bg-red-500/10 text-red-300 border-red-500/30";
  const label = score <= 20 ? "Basso" : score <= 40 ? "Medio" : score <= 60 ? "Alto" : "Molto alto";
  return <span title={risk?.reasons?.join(" · ")}
    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-widest border ${cls}`}>
    {label} · {score}
  </span>;
}

function StatusBanner({ status }) {
  if (!status) return null;
  const rows = [
    { k: "Ambiente", v: status.app_env, ok: status.app_env !== "production" || status.commerce_enabled },
    { k: "Commerce", v: status.commerce_enabled ? "ON" : "OFF", ok: status.commerce_enabled },
    { k: "PSP (Nexi)", v: status.psp_configured ? "configurato" : "MANCA credenziali", ok: status.psp_configured },
    { k: "Email (Brevo)", v: status.email_configured ? "configurato" : "MANCA API key", ok: status.email_configured },
    { k: "Approvati", v: `${status.approved_products}`, ok: status.approved_products > 0 },
    { k: "Feedable (per Google)", v: `${status.feedable_products}`, ok: status.feedable_products > 0 },
  ];
  return (
    <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
      <p className="label-eyebrow mb-3">Stato go-live</p>
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        {rows.map(r => (
          <div key={r.k} className="text-center">
            <p className="text-[10px] font-mono uppercase tracking-widest text-zinc-500">{r.k}</p>
            <p className={`font-mono mt-1 text-sm ${r.ok ? "text-emerald-300" : "text-orange-300"}`}>
              {r.v}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function LicenseImportModal({ sku, onClose, onImported, m }) {
  const [keysText, setKeysText] = useState("");
  const [busy, setBusy] = useState(false);
  const run = async () => {
    const keys = keysText.split("\n").map(k => k.trim()).filter(Boolean);
    if (!keys.length) return;
    setBusy(true);
    try {
      const r = await m.importLicenses({ sku, keys, source: "manual" });
      toast.success(`Importate ${r.imported} chiavi · stock: ${r.available_now}`);
      onImported && onImported(r);
      onClose();
    } catch (e) {
      toast.error("Errore import: " + (e?.response?.data?.detail || e.message));
    } finally { setBusy(false); }
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={onClose}>
      <div className="w-full max-w-lg rounded-xl border border-white/10 bg-[#0A0A0C]" onClick={e => e.stopPropagation()}>
        <div className="p-5 border-b border-white/10 flex items-center justify-between">
          <div>
            <p className="label-eyebrow">Import chiavi</p>
            <h3 className="font-display text-xl">SKU: {sku}</h3>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full"><XCircle size={18}/></button>
        </div>
        <div className="p-5 space-y-3">
          <p className="text-sm text-zinc-400">Una chiave per riga. Le chiavi vengono cifrate a riposo con Fernet.</p>
          <textarea rows={10} value={keysText} onChange={e => setKeysText(e.target.value)}
            placeholder="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX&#10;YYYYY-YYYYY-YYYYY-YYYYY-YYYYY"
            className="w-full bg-black/40 border border-white/15 rounded-lg px-3 py-2 text-sm text-white font-mono"/>
          <div className="flex justify-end gap-2">
            <button onClick={onClose} className="pill-btn border border-white/15 text-zinc-400">Annulla</button>
            <button onClick={run} disabled={busy || !keysText.trim()}
              className="pill-btn bg-white text-black disabled:opacity-50">
              <Upload size={14}/> {busy ? "Import…" : "Importa"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ProductRow({ p, onPatch, onImport, m }) {
  const [expand, setExpand] = useState(false);
  const [sellingPrice, setSellingPrice] = useState(p.selling_price_eur ?? "");
  const [sku, setSku] = useState(p.sku || "");
  const [mpn, setMpn] = useState(p.mpn || "");
  const [gtin, setGtin] = useState(p.gtin || "");
  const [gpc, setGpc] = useState(p.google_product_category || "");
  const [imgOk, setImgOk] = useState(!!p.image_rights_approved);
  const [prov, setProv] = useState(p.provenance_status || "unverified");

  const save = async () => {
    try {
      const body = {
        selling_price_eur: sellingPrice ? Number(sellingPrice) : null,
        sku: sku || null, mpn: mpn || null, gtin: gtin || null,
        google_product_category: gpc || null,
        image_rights_approved: imgOk,
        provenance_status: prov,
      };
      const updated = await m.patch(p.slug, body);
      onPatch(updated);
      toast.success("Prodotto aggiornato");
    } catch (e) { toast.error("Errore: " + (e?.response?.data?.detail || e.message)); }
  };

  const toggleApprove = async () => {
    try {
      const updated = await m.patch(p.slug, { merchant_approved: !p.merchant_approved });
      onPatch(updated);
      toast.success(updated.merchant_approved ? "Prodotto approvato" : "Approvazione revocata");
    } catch (e) { toast.error("Errore: " + (e?.response?.data?.detail || e.message)); }
  };

  const canApprove = sku && p.image_url && Number(sellingPrice) > 0 && imgOk;

  return (
    <div className="border-b border-white/5">
      <div className="grid grid-cols-12 gap-3 items-center px-4 py-3 hover:bg-white/[0.03]">
        <div className="col-span-4 min-w-0">
          <p className="text-white truncate">{p.name}</p>
          <p className="text-xs text-zinc-500 font-mono truncate">{p.slug}</p>
        </div>
        <div className="col-span-1"><RiskBadge risk={p._risk}/></div>
        <div className="col-span-1 text-xs font-mono text-zinc-400">{p.sku || "—"}</div>
        <div className="col-span-1 text-xs font-mono text-zinc-400">{p.gtin || "—"}</div>
        <div className="col-span-1 text-sm text-white font-mono">{p.selling_price_eur ? `€${p.selling_price_eur.toFixed(2)}` : "—"}</div>
        <div className="col-span-1 text-xs font-mono text-zinc-400">
          <span className={p._available_keys > 0 ? "text-emerald-300" : "text-orange-300"}>{p._available_keys}</span> keys
        </div>
        <div className="col-span-1">
          {p.merchant_approved
            ? <span className="inline-flex items-center gap-1 text-emerald-300 text-xs font-mono"><CheckCircle2 size={12}/> approvato</span>
            : <span className="inline-flex items-center gap-1 text-zinc-500 text-xs font-mono"><ShieldAlert size={12}/> draft</span>}
        </div>
        <div className="col-span-2 flex gap-2 justify-end">
          <button onClick={() => setExpand(!expand)}
            className="text-xs font-mono text-zinc-400 hover:text-white">{expand ? "chiudi" : "modifica"}</button>
          <button onClick={toggleApprove}
            disabled={!p.merchant_approved && !canApprove}
            title={!canApprove ? "Servono SKU + prezzo + immagine + diritti immagine" : ""}
            className={`text-xs font-mono px-3 py-1 rounded-full border ${p.merchant_approved ? "border-red-500/30 text-red-300 hover:bg-red-500/10" : "border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/10 disabled:opacity-40 disabled:hover:bg-transparent"}`}>
            {p.merchant_approved ? "revoca" : "approva"}
          </button>
        </div>
      </div>

      {expand && (
        <div className="px-4 pb-4 bg-black/20 grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="label-eyebrow block mb-1">Selling price (€)</label>
            <input type="number" step="0.01" value={sellingPrice} onChange={e => setSellingPrice(e.target.value)}
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-sm text-white"/>
          </div>
          <div>
            <label className="label-eyebrow block mb-1">SKU</label>
            <input value={sku} onChange={e => setSku(e.target.value)}
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-sm text-white font-mono"/>
          </div>
          <div>
            <label className="label-eyebrow block mb-1">MPN</label>
            <input value={mpn} onChange={e => setMpn(e.target.value)}
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-sm text-white font-mono"/>
          </div>
          <div>
            <label className="label-eyebrow block mb-1">GTIN (opzionale)</label>
            <input value={gtin} onChange={e => setGtin(e.target.value)}
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-sm text-white font-mono"/>
          </div>
          <div>
            <label className="label-eyebrow block mb-1">Google product category</label>
            <input value={gpc} onChange={e => setGpc(e.target.value)}
              placeholder="es. 5299 · Software > Antivirus"
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-sm text-white"/>
          </div>
          <div>
            <label className="label-eyebrow block mb-1">Provenance</label>
            <select value={prov} onChange={e => setProv(e.target.value)}
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-sm text-white">
              <option value="unverified">unverified</option>
              <option value="pending">pending</option>
              <option value="verified">verified</option>
            </select>
          </div>
          <div className="md:col-span-3 flex items-center justify-between mt-2 pt-3 border-t border-white/5">
            <label className="flex items-center gap-2 text-sm text-zinc-300">
              <input type="checkbox" checked={imgOk} onChange={e => setImgOk(e.target.checked)}/>
              Diritti immagine documentati
            </label>
            <div className="flex gap-2">
              <button onClick={() => sku && onImport(sku)} disabled={!sku}
                className="pill-btn border border-white/15 text-zinc-300 hover:text-white disabled:opacity-50">
                <KeyRound size={14}/> Import chiavi
              </button>
              <button onClick={save} className="pill-btn bg-white text-black">Salva</button>
            </div>
          </div>
          {p._risk?.reasons?.length > 0 && (
            <div className="md:col-span-3 text-xs text-zinc-500 flex items-start gap-2">
              <Info size={12} className="mt-0.5"/>
              <span>Motivi risk: {p._risk.reasons.join(" · ")}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function AdminMerchant() {
  const { token } = useAdminAuth();
  const m = useMerchant(token);
  const [status, setStatus] = useState(null);
  const [data, setData] = useState(null);
  const [q, setQ] = useState("");
  const [onlyPending, setOnlyPending] = useState(true);
  const [maxRisk, setMaxRisk] = useState(50);
  const [importSku, setImportSku] = useState(null);

  const load = () => {
    const params = { limit: 500 };
    if (onlyPending) params.only_pending = true;
    if (maxRisk) params.max_risk = maxRisk;
    m.queue(params).then(setData);
    m.status().then(setStatus);
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [onlyPending, maxRisk]);

  const filtered = useMemo(() => {
    if (!data) return [];
    if (!q) return data.items;
    const s = q.toLowerCase();
    return data.items.filter(p =>
      p.name.toLowerCase().includes(s) ||
      p.slug.toLowerCase().includes(s) ||
      (p.brand || "").toLowerCase().includes(s) ||
      (p.sku || "").toLowerCase().includes(s));
  }, [data, q]);

  const bulkApproveLowRisk = async () => {
    const candidates = filtered.filter(p => !p.merchant_approved && p._risk.score <= 20 && p.selling_price_eur && p.sku && p.image_url && p.image_rights_approved);
    if (!candidates.length) {
      toast.info("Nessun prodotto passa i criteri (risk ≤ 20 + campi completi + diritti immagine).");
      return;
    }
    if (!window.confirm(`Approvare ${candidates.length} prodotti a basso rischio?`)) return;
    const r = await m.bulkApprove({ slugs: candidates.map(x => x.slug), merchant_approved: true });
    toast.success(`Approvati ${r.modified} prodotti`);
    load();
  };

  return (
    <div className="space-y-6" data-testid="admin-merchant-page">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <p className="label-eyebrow mb-2">Merchant workflow</p>
          <h1 className="font-display text-3xl md:text-4xl tracking-tight">Approvazione prodotti</h1>
          <p className="text-sm text-zinc-500 mt-1">Solo prodotti approvati (merchant_approved + immagine documentata + stock &gt; 0) sono pubblicati.</p>
        </div>
      </div>

      <StatusBanner status={status}/>

      <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-4 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500"/>
          <input value={q} onChange={e => setQ(e.target.value)} data-testid="merchant-search"
            placeholder="Cerca per nome, slug, brand, SKU…"
            className="w-full bg-black/40 border border-white/15 rounded-lg pl-9 pr-3 py-2 text-sm text-white"/>
        </div>
        <label className="flex items-center gap-2 text-sm text-zinc-300">
          <input type="checkbox" checked={onlyPending} onChange={e => setOnlyPending(e.target.checked)}/>
          Solo da approvare
        </label>
        <label className="flex items-center gap-2 text-sm text-zinc-300">
          <Filter size={14} className="text-zinc-500"/>
          Max risk
          <input type="number" min={0} max={100} value={maxRisk} onChange={e => setMaxRisk(Number(e.target.value))}
            className="w-16 bg-black/40 border border-white/15 rounded px-2 py-1 text-sm text-white"/>
        </label>
        <button onClick={bulkApproveLowRisk}
          className="pill-btn bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/20">
          <TrendingUp size={14}/> Approva basso rischio
        </button>
      </div>

      <div className="rounded-xl border border-white/10 bg-[#0B0B0D] overflow-hidden">
        <div className="grid grid-cols-12 gap-3 items-center px-4 py-3 bg-black/40 border-b border-white/10 text-[10px] font-mono uppercase tracking-widest text-zinc-400">
          <div className="col-span-4">Prodotto</div>
          <div className="col-span-1">Risk</div>
          <div className="col-span-1">SKU</div>
          <div className="col-span-1">GTIN</div>
          <div className="col-span-1">Prezzo</div>
          <div className="col-span-1">Stock</div>
          <div className="col-span-1">Stato</div>
          <div className="col-span-2 text-right">Azioni</div>
        </div>
        {!data && <div className="p-8 text-center text-zinc-500">Caricamento…</div>}
        {data && filtered.length === 0 && <div className="p-8 text-center text-zinc-500">Nessun prodotto.</div>}
        {filtered.map(p => (
          <ProductRow key={p.slug} p={p} m={m}
            onPatch={updated => setData(d => ({ ...d, items: d.items.map(x => x.slug === updated.slug ? { ...x, ...updated, _risk: x._risk, _available_keys: x._available_keys } : x) }))}
            onImport={sku => setImportSku(sku)}/>
        ))}
      </div>

      {importSku && (
        <LicenseImportModal sku={importSku} m={m}
          onClose={() => setImportSku(null)}
          onImported={() => load()}/>
      )}
    </div>
  );
}
