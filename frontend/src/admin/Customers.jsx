import { useEffect, useState } from "react";
import { adminApi, useAdminAuth } from "./auth.jsx";
import { Search, ChevronLeft } from "lucide-react";

const money = (n) => new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(n || 0);

export default function AdminCustomers() {
  const { token } = useAdminAuth();
  const api = adminApi(token);
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState(null);

  useEffect(() => { api.customers(q).then(setItems); /* eslint-disable-next-line */ }, [q]);

  if (selected) return <CustomerDetail email={selected} onBack={() => setSelected(null)} api={api} />;

  return (
    <div className="space-y-6" data-testid="admin-customers-page">
      <div>
        <p className="label-eyebrow mb-2">CRM</p>
        <h1 className="font-display text-3xl md:text-4xl tracking-tight">Clienti</h1>
        <p className="text-sm text-zinc-500 mt-1">{items.length} clienti unici (basato sugli ordini).</p>
      </div>

      <div className="flex items-center gap-2 bg-[#0B0B0D] border border-white/10 rounded-full px-3 py-2">
        <Search size={16} className="text-zinc-500" />
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Cerca per email, nome o cognome…"
          className="bg-transparent w-full text-sm text-white placeholder:text-zinc-500 focus:outline-none" />
      </div>

      <div className="rounded-xl border border-white/10 bg-[#0B0B0D] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px] text-sm">
            <thead className="bg-white/[0.03] text-zinc-400 text-xs font-mono uppercase tracking-widest">
              <tr>
                <th className="text-left px-4 py-3">Email</th>
                <th className="text-left px-4 py-3">Nome</th>
                <th className="text-left px-4 py-3">Paese</th>
                <th className="text-right px-4 py-3">Ordini</th>
                <th className="text-right px-4 py-3">Fatturato</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr><td colSpan={5} className="text-center py-8 text-zinc-500">Nessun cliente ancora.</td></tr>
              ) : items.map(c => (
                <tr key={c.email} onClick={() => setSelected(c.email)}
                  data-testid={`customer-row-${c.email}`}
                  className="border-t border-white/5 hover:bg-white/[0.03] cursor-pointer">
                  <td className="px-4 py-3 text-white">{c.email}</td>
                  <td className="px-4 py-3 text-zinc-300">{c.first_name} {c.last_name}</td>
                  <td className="px-4 py-3 text-zinc-400">{c.country}</td>
                  <td className="px-4 py-3 text-right font-mono">{c.orders}</td>
                  <td className="px-4 py-3 text-right font-mono text-white">{money(c.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function CustomerDetail({ email, onBack, api }) {
  const [c, setC] = useState(null);
  useEffect(() => { api.customer(email).then(setC); /* eslint-disable-next-line */ }, [email]);
  if (!c) return <div className="text-zinc-500">Caricamento…</div>;
  return (
    <div className="space-y-6" data-testid="admin-customer-detail">
      <button onClick={onBack} className="text-xs font-mono text-zinc-400 hover:text-white inline-flex items-center gap-1">
        <ChevronLeft size={14}/> Torna ai clienti
      </button>
      <div>
        <p className="label-eyebrow mb-2">Cliente</p>
        <h1 className="font-display text-2xl md:text-3xl tracking-tight">{c.first_name} {c.last_name}</h1>
        <p className="text-sm text-zinc-500 mt-1">{c.email}{c.company ? ` · ${c.company}` : ""}{c.country ? ` · ${c.country}` : ""}</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-4">
          <p className="label-eyebrow mb-1">Ordini</p>
          <p className="font-display text-3xl">{c.orders.length}</p>
        </div>
        <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-4">
          <p className="label-eyebrow mb-1">Fatturato</p>
          <p className="font-display text-3xl">{money(c.total_revenue)}</p>
        </div>
      </div>
      <div className="rounded-xl border border-white/10 bg-[#0B0B0D] overflow-hidden">
        <div className="px-4 py-3 border-b border-white/10 label-eyebrow">Ordini</div>
        {c.orders.map(o => (
          <div key={o.reference} className="border-b border-white/5 p-4 flex items-center justify-between">
            <div>
              <p className="font-mono text-white">{o.reference}</p>
              <p className="text-xs text-zinc-500">{o.created_at?.slice(0, 10)} · {o.items?.length} articoli</p>
            </div>
            <p className="font-mono text-white">{money(o.total_eur)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
