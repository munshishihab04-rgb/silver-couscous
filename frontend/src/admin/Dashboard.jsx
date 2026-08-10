import { useEffect, useState } from "react";
import { adminApi, useAdminAuth } from "./auth.jsx";
import { Users, Eye, ShoppingCart, ArrowUpRight, Circle, PackageCheck, LifeBuoy } from "lucide-react";
import { Link } from "react-router-dom";

const money = (n) => new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(n || 0);

const KpiCard = ({ icon: Icon, label, value, sub, testid }) => (
  <div data-testid={testid} className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
    <div className="flex items-center justify-between text-zinc-400 mb-3">
      <span className="label-eyebrow">{label}</span>
      <Icon size={16} />
    </div>
    <p className="font-display text-3xl md:text-4xl tracking-tight text-white">{value}</p>
    {sub && <p className="text-xs text-zinc-500 mt-1">{sub}</p>}
  </div>
);

export default function AdminDashboard() {
  const { token } = useAdminAuth();
  const api = adminApi(token);
  const [range, setRange] = useState("7d");
  const [data, setData] = useState(null);
  const [live, setLive] = useState(null);
  const [tickets, setTickets] = useState([]);

  useEffect(() => { api.dashboardOverview(range).then(setData); /* eslint-disable-next-line */ }, [range]);
  useEffect(() => {
    api.liveAnalytics().then(setLive);
    api.tickets("open").then(setTickets);
    const t = setInterval(() => api.liveAnalytics().then(setLive), 15000);
    return () => clearInterval(t);
    // eslint-disable-next-line
  }, []);

  if (!data) return <div className="text-zinc-500">Caricamento…</div>;
  const k = data.kpis;

  return (
    <div className="space-y-8" data-testid="admin-dashboard">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <p className="label-eyebrow mb-2">Overview</p>
          <h1 className="font-display text-3xl md:text-4xl tracking-tight">Dashboard</h1>
        </div>
        <div className="flex items-center gap-2">
          {["24h", "7d", "30d", "90d"].map(r => (
            <button key={r} onClick={() => setRange(r)} data-testid={`range-${r}`}
              className={`px-3 py-1.5 rounded-full text-xs font-mono border transition-colors ${range === r ? "bg-white text-black border-white" : "border-white/15 text-zinc-400 hover:text-white"}`}>
              {r}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KpiCard testid="kpi-visitors" icon={Users} label="Visitatori" value={k.unique_visitors} sub={`${k.page_views} pageviews`} />
        <KpiCard testid="kpi-atc" icon={ShoppingCart} label="Add to cart" value={k.add_to_cart} sub={`${k.checkouts} checkout iniziati`} />
        <KpiCard testid="kpi-orders" icon={PackageCheck} label="Ordini" value={k.orders} sub="demo mode" />
        <KpiCard testid="kpi-revenue" icon={ArrowUpRight} label="Fatturato" value={money(k.revenue_eur)} sub="totale periodo" />
      </div>

      {/* Live */}
      <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Circle size={7} className="fill-green-400 text-green-400 animate-pulse" />
            <p className="label-eyebrow">Attività in tempo reale</p>
          </div>
          <p className="text-sm text-white font-mono">{live?.active_visitors ?? "–"} attivi</p>
        </div>
        <div className="space-y-1 max-h-56 overflow-y-auto pr-1">
          {(live?.recent_events || []).slice(0, 15).map((e, i) => (
            <div key={i} className="flex items-center justify-between text-xs font-mono border-b border-white/5 py-1.5">
              <span className="text-zinc-500 truncate mr-3">{e.ts?.slice(11, 19)} · {e.event_type}</span>
              <span className="text-zinc-300 truncate">{e.path || e.product_slug || ""}</span>
            </div>
          ))}
          {(!live || (live.recent_events || []).length === 0) && (
            <p className="text-sm text-zinc-500 py-6 text-center">Nessuna attività recente.</p>
          )}
        </div>
      </div>

      {/* Two-column */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
          <div className="flex items-center justify-between mb-4">
            <p className="label-eyebrow">Top pagine</p>
            <span className="text-xs font-mono text-zinc-500">{data.top_pages.length}</span>
          </div>
          <div className="space-y-2 text-sm">
            {data.top_pages.length === 0 && <p className="text-zinc-500 text-xs">Nessun dato ancora.</p>}
            {data.top_pages.map(p => (
              <div key={p.path} className="flex justify-between border-b border-white/5 pb-2">
                <span className="text-zinc-300 truncate mr-3">{p.path}</span>
                <span className="font-mono text-white">{p.views}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
          <div className="flex items-center justify-between mb-4">
            <p className="label-eyebrow">Top prodotti</p>
            <span className="text-xs font-mono text-zinc-500">{data.top_products.length}</span>
          </div>
          <div className="space-y-2 text-sm">
            {data.top_products.length === 0 && <p className="text-zinc-500 text-xs">Nessun dato ancora.</p>}
            {data.top_products.map(p => (
              <div key={p.slug} className="flex justify-between border-b border-white/5 pb-2">
                <Link to={`/admin/products?q=${p.slug}`} className="text-zinc-300 truncate mr-3 hover:text-white">{p.slug}</Link>
                <span className="font-mono text-white">{p.views}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tickets */}
      <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2"><LifeBuoy size={14}/> <p className="label-eyebrow">Ticket aperti</p></div>
          <Link to="/admin/tickets" className="text-xs font-mono text-zinc-400 hover:text-white">Vedi tutti →</Link>
        </div>
        {tickets.length === 0 ? <p className="text-sm text-zinc-500">Nessun ticket aperto.</p> :
          <div className="space-y-2">
            {tickets.slice(0, 5).map(t => (
              <Link key={t.id} to={`/admin/tickets`} className="block border-b border-white/5 pb-2 hover:bg-white/[0.03] px-2 py-1 rounded">
                <p className="text-white text-sm">{t.subject}</p>
                <p className="text-xs text-zinc-500 font-mono">{t.email} · {t.created_at?.slice(0, 10)}</p>
              </Link>
            ))}
          </div>
        }
      </div>
    </div>
  );
}
