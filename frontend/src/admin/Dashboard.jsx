import { useEffect, useState } from "react";
import { adminApi, useAdminAuth } from "./auth.jsx";
import {
  Users, ShoppingCart, ArrowUpRight, Circle, PackageCheck, LifeBuoy,
  ShoppingBag, Download, TrendingUp,
} from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import {
  ResponsiveContainer, AreaChart, Area, LineChart, Line, XAxis, YAxis,
  Tooltip, CartesianGrid, PieChart, Pie, Cell, Legend, BarChart, Bar,
} from "recharts";

const money = (n) => new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(n || 0);

const KpiCard = ({ icon: Icon, label, value, sub, testid, accent = "text-white" }) => (
  <div data-testid={testid} className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5 hover:border-white/20 transition-colors">
    <div className="flex items-center justify-between text-zinc-400 mb-3">
      <span className="label-eyebrow">{label}</span>
      <Icon size={16} />
    </div>
    <p className={`font-display text-3xl md:text-4xl tracking-tight ${accent}`}>{value}</p>
    {sub && <p className="text-xs text-zinc-500 mt-1">{sub}</p>}
  </div>
);

const CHART_COLORS = {
  primary: "#ffffff",
  primaryDim: "rgba(255,255,255,0.4)",
  secondary: "#a78bfa",
  accent: "#34d399",
  warn: "#fbbf24",
  danger: "#f87171",
  grid: "rgba(255,255,255,0.08)",
  axis: "#71717a",
};

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-white/15 bg-[#0A0A0C] px-3 py-2 text-xs font-mono">
      <p className="text-zinc-400 mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="text-white flex items-center gap-2">
          <span className="w-2 h-2 rounded-full inline-block" style={{ background: p.color }} />
          {p.name}: <span className="text-white font-semibold">{p.value}</span>
        </p>
      ))}
    </div>
  );
}

const DEVICE_COLORS = ["#ffffff", "#a78bfa", "#34d399", "#fbbf24"];

export default function AdminDashboard() {
  const { token } = useAdminAuth();
  const api = adminApi(token);
  const [range, setRange] = useState("7d");
  const [data, setData] = useState(null);
  const [live, setLive] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [recentOrders, setRecentOrders] = useState([]);

  useEffect(() => { api.dashboardOverview(range).then(setData); /* eslint-disable-next-line */ }, [range]);
  useEffect(() => {
    api.liveAnalytics().then(setLive);
    api.tickets("open").then(setTickets);
    api.orders({ limit: 5 }).then(r => setRecentOrders(r.items || [])).catch(() => setRecentOrders([]));
    const t = setInterval(() => api.liveAnalytics().then(setLive), 15000);
    return () => clearInterval(t);
    // eslint-disable-next-line
  }, []);

  if (!data) return <div className="text-zinc-500">Caricamento…</div>;
  const k = data.kpis;

  const deviceData = Object.entries(data.devices || {})
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), value }));

  const tsData = (data.timeseries || []).map(t => ({
    date: t.date.slice(5),
    visitors: t.visitors,
    pageviews: t.page_views,
  }));

  const exportAll = async (kind) => {
    try {
      const filename = await api.downloadExport(kind);
      toast.success(`Esportato: ${filename}`);
    } catch { toast.error("Errore export"); }
  };

  return (
    <div className="space-y-8" data-testid="admin-dashboard">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <p className="label-eyebrow mb-2">Overview</p>
          <h1 className="font-display text-3xl md:text-4xl tracking-tight">Dashboard</h1>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
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
        <KpiCard testid="kpi-atc" icon={ShoppingCart} label="Add to cart" value={k.add_to_cart} sub={`${k.checkouts} checkout`} />
        <KpiCard testid="kpi-orders" icon={PackageCheck} label="Ordini" value={k.orders} sub="periodo selezionato" />
        <KpiCard testid="kpi-revenue" icon={ArrowUpRight} label="Fatturato" value={money(k.revenue_eur)} sub="totale periodo" accent="text-emerald-300" />
      </div>

      {/* Visitor timeseries chart */}
      <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2"><TrendingUp size={14} className="text-zinc-400"/><p className="label-eyebrow">Andamento visitatori</p></div>
          <button onClick={() => exportAll("analytics")} className="text-xs font-mono text-zinc-400 hover:text-white flex items-center gap-1">
            <Download size={12}/> CSV
          </button>
        </div>
        {tsData.length === 0 ? (
          <p className="text-sm text-zinc-500 py-10 text-center">Nessun dato ancora — apri il sito pubblico per generare eventi.</p>
        ) : (
          <div style={{ width: "100%", height: 260 }}>
            <ResponsiveContainer>
              <AreaChart data={tsData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="gradVisitors" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.35}/>
                    <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="gradPV" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.secondary} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={CHART_COLORS.secondary} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid stroke={CHART_COLORS.grid} vertical={false}/>
                <XAxis dataKey="date" stroke={CHART_COLORS.axis} tick={{ fontSize: 10, fontFamily: "monospace" }} axisLine={false} tickLine={false}/>
                <YAxis stroke={CHART_COLORS.axis} tick={{ fontSize: 10, fontFamily: "monospace" }} axisLine={false} tickLine={false} allowDecimals={false}/>
                <Tooltip content={<ChartTooltip/>} cursor={{ stroke: "rgba(255,255,255,0.1)" }}/>
                <Area type="monotone" dataKey="visitors" name="Visitatori" stroke={CHART_COLORS.primary} strokeWidth={2} fill="url(#gradVisitors)"/>
                <Area type="monotone" dataKey="pageviews" name="Pageviews" stroke={CHART_COLORS.secondary} strokeWidth={2} fill="url(#gradPV)"/>
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Two-column: devices + top products */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5 lg:col-span-1">
          <p className="label-eyebrow mb-3">Dispositivi</p>
          {deviceData.length === 0 ? <p className="text-sm text-zinc-500 py-8 text-center">Nessun dato.</p> : (
            <div style={{ width: "100%", height: 220 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={deviceData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                    innerRadius={55} outerRadius={80} paddingAngle={2}>
                    {deviceData.map((_, i) => <Cell key={i} fill={DEVICE_COLORS[i % DEVICE_COLORS.length]} stroke="#0B0B0D"/>)}
                  </Pie>
                  <Tooltip content={<ChartTooltip/>}/>
                  <Legend wrapperStyle={{ fontSize: 11, fontFamily: "monospace", color: "#a1a1aa" }}/>
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <p className="label-eyebrow">Top prodotti visti</p>
            <span className="text-xs font-mono text-zinc-500">{data.top_products.length}</span>
          </div>
          {data.top_products.length === 0 ? <p className="text-sm text-zinc-500 py-8">Nessun dato ancora.</p> : (
            <div style={{ width: "100%", height: 220 }}>
              <ResponsiveContainer>
                <BarChart data={data.top_products.slice(0, 8)} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 0 }}>
                  <CartesianGrid stroke={CHART_COLORS.grid} horizontal={false}/>
                  <XAxis type="number" stroke={CHART_COLORS.axis} tick={{ fontSize: 10, fontFamily: "monospace" }} axisLine={false} tickLine={false} allowDecimals={false}/>
                  <YAxis type="category" dataKey="slug" stroke={CHART_COLORS.axis}
                    tick={{ fontSize: 10, fontFamily: "monospace", fill: "#a1a1aa" }} width={140} axisLine={false} tickLine={false}/>
                  <Tooltip content={<ChartTooltip/>} cursor={{ fill: "rgba(255,255,255,0.03)" }}/>
                  <Bar dataKey="views" name="Views" fill={CHART_COLORS.primary} radius={[0, 4, 4, 0]}/>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Recent orders + live */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2"><ShoppingBag size={14} className="text-zinc-400"/><p className="label-eyebrow">Ordini recenti</p></div>
            <Link to="/admin/orders" className="text-xs font-mono text-zinc-400 hover:text-white">Vedi tutti →</Link>
          </div>
          {recentOrders.length === 0 ? (
            <p className="text-sm text-zinc-500 py-6">Nessun ordine ancora.</p>
          ) : (
            <div className="space-y-1">
              {recentOrders.map(o => (
                <Link key={o.reference} to="/admin/orders"
                  className="flex items-center justify-between border-b border-white/5 pb-2 pt-1 hover:bg-white/[0.03] px-2 rounded transition-colors">
                  <div className="min-w-0">
                    <p className="font-mono text-white text-sm truncate">{o.reference}</p>
                    <p className="text-xs text-zinc-500 truncate">{o.email}</p>
                  </div>
                  <p className="font-mono text-white text-sm shrink-0">{money(o.total_eur)}</p>
                </Link>
              ))}
            </div>
          )}
        </div>

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
      </div>

      {/* Top pages + Tickets */}
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

      {/* Quick export buttons */}
      <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
        <p className="label-eyebrow mb-3">Esportazioni rapide</p>
        <div className="flex flex-wrap gap-2">
          {[
            { k: "orders", l: "Ordini" },
            { k: "customers", l: "Clienti" },
            { k: "products", l: "Prodotti" },
            { k: "analytics", l: "Eventi analytics" },
          ].map(x => (
            <button key={x.k} onClick={() => exportAll(x.k)} data-testid={`dashboard-export-${x.k}`}
              className="pill-btn border border-white/15 text-zinc-300 hover:text-white hover:border-white/40">
              <Download size={12}/> {x.l}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
