import { useEffect, useState } from "react";
import { adminApi, useAdminAuth } from "./auth.jsx";
import { toast } from "sonner";
import { Circle, Check, Save, Loader2 } from "lucide-react";

const statusMeta = {
  open: { label: "Aperto", color: "text-orange-300 bg-orange-500/10 border-orange-500/30" },
  in_progress: { label: "In lavorazione", color: "text-blue-300 bg-blue-500/10 border-blue-500/30" },
  closed: { label: "Chiuso", color: "text-zinc-400 bg-white/[0.04] border-white/10" },
};

export default function AdminTickets() {
  const { token } = useAdminAuth();
  const api = adminApi(token);
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("");
  const [selected, setSelected] = useState(null);
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);

  const load = () => api.tickets(filter || undefined).then(setItems);
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [filter]);

  const update = async (id, patch) => {
    setSaving(true);
    try {
      await api.updateTicket(id, patch);
      toast.success("Aggiornato");
      load();
      if (selected?.id === id) setSelected({ ...selected, ...patch });
    } catch { toast.error("Errore"); }
    finally { setSaving(false); }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-4" data-testid="admin-tickets-page">
      <div>
        <div className="mb-4">
          <p className="label-eyebrow mb-2">Support</p>
          <h1 className="font-display text-3xl tracking-tight">Ticket</h1>
        </div>
        <div className="flex gap-2 mb-3 flex-wrap">
          {["", "open", "in_progress", "closed"].map(s => (
            <button key={s} onClick={() => setFilter(s)} data-testid={`ticket-filter-${s || 'all'}`}
              className={`chip ${filter === s ? "!bg-white !text-black !border-white" : ""}`}>
              {s === "" ? "Tutti" : statusMeta[s].label}
            </button>
          ))}
        </div>
        <div className="rounded-xl border border-white/10 bg-[#0B0B0D] overflow-hidden">
          {items.length === 0 ? (
            <p className="p-6 text-sm text-zinc-500 text-center">Nessun ticket.</p>
          ) : items.map(t => {
            const st = statusMeta[t.status || "open"];
            const active = selected?.id === t.id;
            return (
              <button key={t.id} onClick={() => { setSelected(t); setNotes(t.admin_notes || ""); }}
                data-testid={`ticket-item-${t.id}`}
                className={`w-full text-left px-4 py-3 border-b border-white/5 transition-colors ${active ? "bg-white/[0.05]" : "hover:bg-white/[0.03]"}`}>
                <div className="flex items-start justify-between gap-2 mb-1">
                  <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border ${st.color}`}>{st.label}</span>
                  <span className="text-[10px] font-mono text-zinc-500">{t.created_at?.slice(5, 10)}</span>
                </div>
                <p className="text-white text-sm truncate">{t.subject}</p>
                <p className="text-xs text-zinc-500 truncate">{t.email}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Detail */}
      <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-6">
        {!selected ? (
          <p className="text-zinc-500 text-sm">Seleziona un ticket per vedere i dettagli.</p>
        ) : (
          <div className="space-y-5">
            <div className="flex items-start justify-between gap-3 flex-wrap">
              <div>
                <p className="label-eyebrow">{selected.email}</p>
                <h2 className="font-display text-2xl mt-1">{selected.subject}</h2>
                <p className="text-xs text-zinc-500 mt-1">{selected.created_at}</p>
              </div>
              <div className="flex gap-2">
                {Object.entries(statusMeta).map(([k, v]) => (
                  <button key={k} onClick={() => update(selected.id, { status: k })}
                    data-testid={`ticket-status-${k}`}
                    className={`chip ${selected.status === k ? "!bg-white !text-black !border-white" : ""}`}>
                    {v.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="label-eyebrow mb-2">Messaggio</p>
              <div className="rounded-md border border-white/10 p-4 whitespace-pre-wrap text-zinc-300 bg-black/30">{selected.message}</div>
            </div>
            <div>
              <p className="label-eyebrow mb-2">Note interne</p>
              <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={4} data-testid="ticket-notes"
                className="w-full bg-black border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none focus:border-white/30" />
              <button onClick={() => update(selected.id, { admin_notes: notes })} disabled={saving} data-testid="ticket-save-notes"
                className="pill-btn bg-white text-black hover:bg-zinc-200 mt-3 disabled:opacity-50">
                {saving ? <Loader2 size={14} className="animate-spin"/> : <Save size={14}/>} Salva note
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
