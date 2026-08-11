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
    { k: "Candidati pilota", v: `${status.pilot_candidates}`, ok: status.pilot_candidates > 0 },
    { k: "Schede pilota approvate", v: `${status.catalog_review_approved}`, ok: status.catalog_review_approved > 0 },
    { k: "Provenienza verificata", v: `${status.provenance_evidence_verified}`, ok: status.provenance_evidence_verified > 0 },
    { k: "Diritti immagini", v: `${status.image_rights_evidence_verified}`, ok: status.image_rights_evidence_verified > 0 },
    { k: "Feedable (per Google)", v: `${status.feedable_products}`, ok: status.feedable_products > 0 },
  ];
  return (
    <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
      <p className="label-eyebrow mb-3">Stato go-live</p>
      <div className="grid grid-cols-2 md:grid-cols-5 xl:grid-cols-10 gap-3">
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
  const [mpn, setMpn] = useState(p.mpn || p.mpn_candidate_private || "");
  const [gtin, setGtin] = useState(p.gtin || p.gtin_candidate_private || "");
  const [mpnStatus, setMpnStatus] = useState(p.mpn_status || "assignment_unverified");
  const [gtinStatus, setGtinStatus] = useState(p.gtin_status || "assignment_unverified");
  const [gpc, setGpc] = useState(p.google_product_category || "");
  const [imgOk, setImgOk] = useState(!!p.image_rights_approved);
  const [prov, setProv] = useState(p.provenance_status || "unverified");
  const [catalogReview, setCatalogReview] = useState(p.catalog_review_status || "pending");
  const [supplierName, setSupplierName] = useState(p.provenance_evidence_private?.supplier_name || "");
  const [sourceType, setSourceType] = useState(p.provenance_evidence_private?.source_type || "");
  const [provenanceRefs, setProvenanceRefs] = useState((p.provenance_evidence_private?.evidence_refs || []).join("\n"));
  const [rightsBasis, setRightsBasis] = useState(p.image_rights_evidence_private?.rights_basis || "");
  const [imageRefs, setImageRefs] = useState((p.image_rights_evidence_private?.evidence_refs || []).join("\n"));

  const save = async () => {
    try {
      const body = {
        selling_price_eur: sellingPrice ? Number(sellingPrice) : null,
        sku: sku || null, mpn: mpn || null, gtin: gtin || null,
        mpn_status: mpn ? mpnStatus : null,
        gtin_status: gtin ? gtinStatus : null,
        google_product_category: gpc || null,
        catalog_review_status: catalogReview,
        image_rights_approved: imgOk,
        provenance_status: prov,
        provenance_evidence_private: {
          supplier_name: supplierName || null,
          source_type: sourceType || null,
          evidence_refs: provenanceRefs.split("\n").map(v => v.trim()).filter(Boolean),
        },
        image_rights_evidence_private: {
          ...(p.image_rights_evidence_private || {}),
          rights_basis: rightsBasis || null,
          evidence_refs: imageRefs.split("\n").map(v => v.trim()).filter(Boolean),
        },
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

  const identifierVerified = (gtin && gtinStatus === "verified") || (mpn && mpnStatus === "verified");
  const evidenceComplete = supplierName && sourceType && provenanceRefs.trim() && rightsBasis && imageRefs.trim();
  const canApprove = sku && p.image_url && Number(sellingPrice) > 0 && imgOk && prov === "verified" && identifierVerified && evidenceComplete && catalogReview === "approved" && p.stock > 0;

  return (
    <div className="border-b border-white/5">
      <div className="grid grid-cols-12 gap-3 items-center px-4 py-3 hover:bg-white/[0.03]">
        <div className="col-span-4 min-w-0">
          <p className="text-white truncate">{p.name}</p>
          <p className="text-xs text-zinc-500 font-mono truncate">
            {p.pilot_candidate_private && <span className="text-cyan-300 mr-2">PILOT #{p.pilot_rank_private}</span>}
            {p.slug}
          </p>
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
            title={!canApprove ? "Servono prezzo, stock, identificatore verificato, provenienza documentata e diritti immagine documentati" : ""}
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
            <select value={mpnStatus} onChange={e => setMpnStatus(e.target.value)} className="mt-1 w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-xs text-white">
              <option value="assignment_unverified">assignment_unverified</option>
              <option value="verified">verified</option>
            </select>
          </div>
          <div>
            <label className="label-eyebrow block mb-1">GTIN (opzionale)</label>
            <input value={gtin} onChange={e => setGtin(e.target.value)}
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-sm text-white font-mono"/>
            <select value={gtinStatus} onChange={e => setGtinStatus(e.target.value)} className="mt-1 w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-xs text-white">
              <option value="assignment_unverified">assignment_unverified</option>
              <option value="duplicate_conflict">duplicate_conflict</option>
              <option value="invalid_checksum">invalid_checksum</option>
              <option value="missing">missing</option>
              <option value="verified">verified</option>
            </select>
          </div>
          <div>
            <label className="label-eyebrow block mb-1">Google product category</label>
            <input value={gpc} onChange={e => setGpc(e.target.value)}
              placeholder="es. 5299 · Software > Antivirus"
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-sm text-white"/>
          </div>
          <div>
            <label className="label-eyebrow block mb-1">Revisione catalogo pilota</label>
            <select value={catalogReview} onChange={e => setCatalogReview(e.target.value)}
              disabled={!p.pilot_candidate_private}
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-sm text-white disabled:opacity-50">
              <option value="not_selected">not_selected</option>
              <option value="pending">pending</option>
              <option value="rejected">rejected</option>
              <option value="approved">approved</option>
            </select>
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
          <div>
            <label className="label-eyebrow block mb-1">Fornitore documentato</label>
            <input value={supplierName} onChange={e => setSupplierName(e.target.value)}
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-sm text-white"/>
          </div>
          <div>
            <label className="label-eyebrow block mb-1">Tipo provenienza</label>
            <select value={sourceType} onChange={e => setSourceType(e.target.value)}
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-sm text-white">
              <option value="">non verificato</option>
              <option value="manufacturer">manufacturer</option>
              <option value="authorized_distributor">authorized_distributor</option>
              <option value="documented_reseller">documented_reseller</option>
            </select>
          </div>
          <div>
            <label className="label-eyebrow block mb-1">Documenti provenienza</label>
            <textarea rows={3} value={provenanceRefs} onChange={e => setProvenanceRefs(e.target.value)}
              placeholder="private://documents/contratto-fornitore"
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-xs text-white font-mono"/>
          </div>
          <div>
            <label className="label-eyebrow block mb-1">Base diritti immagine</label>
            <select value={rightsBasis} onChange={e => setRightsBasis(e.target.value)}
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-sm text-white">
              <option value="">non verificata</option>
              <option value="owned">owned</option>
              <option value="licensed">licensed</option>
              <option value="manufacturer_authorized">manufacturer_authorized</option>
              <option value="public_domain">public_domain</option>
            </select>
          </div>
          <div>
            <label className="label-eyebrow block mb-1">Documenti immagine</label>
            <textarea rows={3} value={imageRefs} onChange={e => setImageRefs(e.target.value)}
              placeholder="private://documents/autorizzazione-immagine"
              className="w-full bg-black/40 border border-white/15 rounded px-2 py-1 text-xs text-white font-mono"/>
          </div>
          <div>
            <label className="label-eyebrow block mb-1">Fingerprint asset</label>
            <p className="text-[11px] text-zinc-500 font-mono break-all">{p.image_rights_evidence_private?.sha256 || "asset non indicizzato"}</p>
            <p className="text-[11px] text-zinc-500">{p.image_rights_evidence_private?.width || "—"} × {p.image_rights_evidence_private?.height || "—"}</p>
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
  const [pilotOnly, setPilotOnly] = useState(true);
  const [maxRisk, setMaxRisk] = useState(100);
  const [importSku, setImportSku] = useState(null);

  const load = () => {
    const params = { limit: 500 };
    if (onlyPending) params.only_pending = true;
    if (pilotOnly) params.pilot_only = true;
    if (maxRisk) params.max_risk = maxRisk;
    m.queue(params).then(setData);
    m.status().then(setStatus);
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [onlyPending, pilotOnly, maxRisk]);

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
    const candidates = filtered.filter(p => !p.merchant_approved && p.catalog_review_status === "approved" && p._risk.score <= 20 && p.selling_price_eur && p.sku && p.image_url && p.image_rights_approved);
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
          <p className="text-sm text-zinc-500 mt-1">Il catalogo pilota richiede revisione documentale; la pubblicazione richiede anche approvazione Merchant e stock reale.</p>
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
        <label className="flex items-center gap-2 text-sm text-cyan-300">
          <input type="checkbox" checked={pilotOnly} onChange={e => setPilotOnly(e.target.checked)}/>
          Solo catalogo pilota
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
