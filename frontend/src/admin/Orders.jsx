import { useEffect, useMemo, useState } from "react";
import { adminApi, useAdminAuth } from "./auth.jsx";
import { Search, Filter, X, Trash2, Download, ChevronDown, ChevronUp } from "lucide-react";
import { toast } from "sonner";

const money = (n) => new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(n || 0);
const fmtDate = (iso) => {
  if (!iso) return "—";
  try { return new Date(iso).toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" }); }
  catch { return iso; }
};

const STATUS_META = {
  pending:         { label: "In sospeso",       cls: "bg-yellow-500/10 text-yellow-300 border-yellow-500/30" },
  demo_confirmed:  { label: "Demo confermata",  cls: "bg-blue-500/10 text-blue-300 border-blue-500/30" },
  paid:            { label: "Pagato",           cls: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" },
  delivered:       { label: "Consegnato",       cls: "bg-teal-500/10 text-teal-300 border-teal-500/30" },
  cancelled:       { label: "Annullato",        cls: "bg-red-500/10 text-red-300 border-red-500/30" },
  refunded:        { label: "Rimborsato",       cls: "bg-fuchsia-500/10 text-fuchsia-300 border-fuchsia-500/30" },
};

const STATUS_OPTIONS = Object.keys(STATUS_META);

function StatusPill({ status }) {
  const m = STATUS_META[status] || { label: status || "—", cls: "bg-white/5 text-zinc-300 border-white/10" };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-widest border ${m.cls}`}>
      {m.label}
    </span>
  );
}

function OrderDetail({ order, onClose, onSaved }) {
  const { token } = useAdminAuth();
  const api = adminApi(token);
  const [status, setStatus] = useState(order.status || "pending");
  const [notes, setNotes] = useState(order.admin_notes || "");
  const [saving, setSaving] = useState(false);

  const save = async () => {
    try {
      setSaving(true);
      const updated = await api.updateOrder(order.reference, { status, admin_notes: notes });
      toast.success("Ordine aggiornato");
      onSaved && onSaved(updated);
    } catch (e) {
      toast.error("Errore durante l'aggiornamento");
    } finally { setSaving(false); }
  };

  const remove = async () => {
    if (!window.confirm(`Eliminare definitivamente l'ordine ${order.reference}?`)) return;
    try {
      await api.deleteOrder(order.reference);
      toast.success("Ordine eliminato");
      onSaved && onSaved(null, true);
    } catch { toast.error("Errore durante l'eliminazione"); }
  };

  return (
    <div className="fixed inset-0 z-50 flex" data-testid="order-detail-drawer">
      <div className="flex-1 bg-black/70" onClick={onClose} />
      <div className="w-full max-w-xl h-full bg-[#0A0A0C] border-l border-white/10 overflow-y-auto">
        <div className="p-5 border-b border-white/10 flex items-center justify-between sticky top-0 bg-[#0A0A0C] z-10">
          <div>
            <p className="label-eyebrow">Ordine</p>
            <h2 className="font-display text-2xl">{order.reference}</h2>
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-white/5"><X size={18}/></button>
        </div>

        <div className="p-5 space-y-6">
          <div className="flex items-center justify-between">
            <StatusPill status={status} />
            <span className="text-xs font-mono text-zinc-500">{fmtDate(order.created_at)}</span>
          </div>

          <div>
            <p className="label-eyebrow mb-2">Cliente</p>
            <div className="rounded-lg border border-white/10 bg-black/30 p-4 text-sm space-y-1">
              <p className="text-white">{order.first_name} {order.last_name}</p>
              <p className="text-zinc-400">{order.email}</p>
              {order.company && <p className="text-zinc-500">{order.company}{order.vat ? ` — P.IVA ${order.vat}` : ""}</p>}
              <p className="text-zinc-500">{order.country}</p>
            </div>
          </div>

          <div>
            <p className="label-eyebrow mb-2">Righe ordine</p>
            <div className="rounded-lg border border-white/10 bg-black/30 divide-y divide-white/5">
              {(order.items || []).map((it, i) => (
                <div key={i} className="p-3 flex justify-between text-sm">
                  <div>
                    <p className="text-white">{it.product_name}</p>
                    <p className="text-zinc-500 text-xs font-mono">{it.variant_label} × {it.quantity}</p>
                  </div>
                  <p className="text-white font-mono">{money(it.unit_price_eur * it.quantity)}</p>
                </div>
              ))}
              <div className="p-3 flex justify-between text-sm border-t border-white/10">
                <span className="text-zinc-400">Subtotale</span>
                <span className="text-white font-mono">{money(order.subtotal_eur)}</span>
              </div>
              <div className="p-3 flex justify-between text-base">
                <span className="text-white font-heading">Totale</span>
                <span className="text-white font-display">{money(order.total_eur)}</span>
              </div>
            </div>
          </div>

          <div>
            <p className="label-eyebrow mb-2">Stato ordine</p>
            <select value={status} onChange={e => setStatus(e.target.value)} data-testid="order-status-select"
              className="w-full bg-black/40 border border-white/15 rounded-lg px-3 py-2 text-sm text-white">
              {STATUS_OPTIONS.map(s => <option key={s} value={s}>{STATUS_META[s].label}</option>)}
            </select>
          </div>

          <div>
            <p className="label-eyebrow mb-2">Note interne</p>
            <textarea rows={4} value={notes} onChange={e => setNotes(e.target.value)}
              placeholder="Aggiungi una nota interna (visibile solo agli admin)…"
              className="w-full bg-black/40 border border-white/15 rounded-lg px-3 py-2 text-sm text-white" />
          </div>

          <div className="flex gap-3 pt-2">
            <button onClick={save} disabled={saving} data-testid="order-save"
              className="pill-btn bg-white text-black hover:bg-zinc-200 flex-1 disabled:opacity-50">
              {saving ? "Salvo…" : "Salva modifiche"}
            </button>
            <button onClick={remove}
              className="pill-btn border border-red-500/40 text-red-300 hover:bg-red-500/10">
              <Trash2 size={14}/> Elimina
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AdminOrders() {
  const { token } = useAdminAuth();
  const api = adminApi(token);
  const [data, setData] = useState({ total: 0, items: [] });
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState(null);
  const [sortBy, setSortBy] = useState({ key: "created_at", dir: "desc" });

  const load = () => {
    setLoading(true);
    const params = {};
    if (q) params.q = q;
    if (status) params.status = status;
    api.orders(params).then(setData).finally(() => setLoading(false));
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [q, status]);

  const sorted = useMemo(() => {
    const items = [...(data.items || [])];
    const { key, dir } = sortBy;
    items.sort((a, b) => {
      let x = a[key], y = b[key];
      if (typeof x === "string") x = x.toLowerCase();
      if (typeof y === "string") y = y.toLowerCase();
      if (x == null) x = "";
      if (y == null) y = "";
      if (x < y) return dir === "asc" ? -1 : 1;
      if (x > y) return dir === "asc" ? 1 : -1;
      return 0;
    });
    return items;
  }, [data, sortBy]);

  const toggleSort = (key) => {
    setSortBy(s => s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" });
  };

  const download = async () => {
    try {
      const params = {};
      if (status) params.status = status;
      const filename = await api.downloadExport("orders", params);
      toast.success(`Esportato: ${filename}`);
    } catch { toast.error("Errore durante l'esportazione"); }
  };

  return (
    <div className="space-y-6" data-testid="admin-orders-page">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <p className="label-eyebrow mb-2">Vendite</p>
          <h1 className="font-display text-3xl md:text-4xl tracking-tight">Ordini</h1>
          <p className="text-sm text-zinc-500 mt-1">{data.total} ordini in totale</p>
        </div>
        <button onClick={download} data-testid="export-orders-csv"
          className="pill-btn border border-white/20 text-white hover:bg-white/5">
          <Download size={14}/> Esporta CSV
        </button>
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-4 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500"/>
          <input
            data-testid="orders-search"
            value={q} onChange={e => setQ(e.target.value)}
            placeholder="Cerca per riferimento, email, nome…"
            className="w-full bg-black/40 border border-white/15 rounded-lg pl-9 pr-3 py-2 text-sm text-white"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter size={14} className="text-zinc-500"/>
          <select value={status} onChange={e => setStatus(e.target.value)} data-testid="orders-status-filter"
            className="bg-black/40 border border-white/15 rounded-lg px-3 py-2 text-sm text-white">
            <option value="">Tutti gli stati</option>
            {STATUS_OPTIONS.map(s => <option key={s} value={s}>{STATUS_META[s].label}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-white/10 bg-[#0B0B0D] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-black/40 border-b border-white/10">
              <tr className="text-left text-zinc-400 text-xs font-mono uppercase tracking-widest">
                {[
                  { k: "reference", l: "Riferimento" },
                  { k: "created_at", l: "Data" },
                  { k: "email", l: "Cliente" },
                  { k: "status", l: "Stato" },
                  { k: "total_eur", l: "Totale" },
                ].map(c => (
                  <th key={c.k} className="px-4 py-3 select-none cursor-pointer" onClick={() => toggleSort(c.k)}>
                    <span className="inline-flex items-center gap-1">{c.l}
                      {sortBy.key === c.k && (sortBy.dir === "asc" ? <ChevronUp size={12}/> : <ChevronDown size={12}/>)}
                    </span>
                  </th>
                ))}
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={6} className="px-4 py-10 text-center text-zinc-500">Caricamento…</td></tr>
              )}
              {!loading && sorted.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-10 text-center text-zinc-500">Nessun ordine.</td></tr>
              )}
              {sorted.map(o => (
                <tr key={o.reference} className="border-b border-white/5 hover:bg-white/[0.03] cursor-pointer"
                  onClick={() => setSelected(o)} data-testid={`order-row-${o.reference}`}>
                  <td className="px-4 py-3 font-mono text-white">{o.reference}</td>
                  <td className="px-4 py-3 text-zinc-400">{fmtDate(o.created_at)}</td>
                  <td className="px-4 py-3">
                    <p className="text-white">{o.first_name} {o.last_name}</p>
                    <p className="text-zinc-500 text-xs">{o.email}</p>
                  </td>
                  <td className="px-4 py-3"><StatusPill status={o.status}/></td>
                  <td className="px-4 py-3 font-mono text-white">{money(o.total_eur)}</td>
                  <td className="px-4 py-3 text-right text-zinc-500">→</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selected && (
        <OrderDetail
          order={selected}
          onClose={() => setSelected(null)}
          onSaved={(updated, removed) => {
            if (removed) { setSelected(null); load(); return; }
            if (updated) {
              setSelected(updated);
              setData(d => ({ ...d, items: d.items.map(x => x.reference === updated.reference ? updated : x) }));
            }
          }}
        />
      )}
    </div>
  );
}
