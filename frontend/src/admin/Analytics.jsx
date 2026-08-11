import { useEffect, useState } from "react";
import { adminApi, useAdminAuth } from "./auth.jsx";
import { Users, Eye, ShoppingCart, PackageCheck, Download } from "lucide-react";
import { toast } from "sonner";
import {
  ResponsiveContainer, LineChart, Line, AreaChart, Area, XAxis, YAxis,
  Tooltip, CartesianGrid, PieChart, Pie, Cell, Legend, BarChart, Bar,
} from "recharts";

const money = (n) => new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(n || 0);

const COLORS = {
  primary: "#ffffff",
  secondary: "#a78bfa",
  accent: "#34d399",
  warn: "#fbbf24",
  danger: "#f87171",
  grid: "rgba(255,255,255,0.08)",
  axis: "#71717a",
};
const REFPIE = ["#ffffff", "#a78bfa", "#34d399", "#fbbf24", "#f87171", "#60a5fa", "#f472b6", "#22d3ee"];

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

const Kpi = ({ label, value, icon: Icon, accent }) => (
  <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-4">
    <div className="flex items-center justify-between text-zinc-400 mb-2">
      <span className="label-eyebrow">{label}</span><Icon size={14}/>
    </div>
    <p className={`font-display text-2xl md:text-3xl ${accent || "text-white"}`}>{value}</p>
  </div>
);

export default function AdminAnalytics() {
  const { token } = useAdminAuth();
  const api = adminApi(token);
  const [range, setRange] = useState("30d");
  const [d, setD] = useState(null);

  useEffect(() => { api.dashboardOverview(range).then(setD); /* eslint-disable-next-line */ }, [range]);

  if (!d) return <div className="text-zinc-500">Caricamento…</div>;
  const k = d.kpis;

  const ts = (d.timeseries || []).map(t => ({
    date: t.date.slice(5),
    visitors: t.visitors,
    pageviews: t.page_views,
    events: t.events,
  }));

  const deviceData = Object.entries(d.devices || {})
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), value }));

  const referrers = (d.referrers || []).slice(0, 8);
  const topPages = (d.top_pages || []).slice(0, 10);
  const topProducts = (d.top_products || []).slice(0, 10);

  const download = async () => {
    try {
      const filename = await api.downloadExport("analytics");
      toast.success(`Esportato: ${filename}`);
    } catch { toast.error("Errore export"); }
  };

  return (
    <div className="space-y-6" data-testid="admin-analytics-page">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <p className="label-eyebrow mb-2">Analytics</p>
          <h1 className="font-display text-3xl md:text-4xl tracking-tight">Comportamento visitatori</h1>
          <p className="text-sm text-zinc-500 mt-1">Dati raccolti dal tracker interno di LicenzPol.</p>
        </div>
        <div className="flex gap-2 items-center flex-wrap">
          {["24h", "7d", "30d", "90d"].map(r => (
            <button key={r} onClick={() => setRange(r)} data-testid={`analytics-range-${r}`}
              className={`chip ${range === r ? "!bg-white !text-black !border-white" : ""}`}>{r}</button>
          ))}
          <button onClick={download} data-testid="export-analytics-csv"
            className="pill-btn border border-white/20 text-white hover:bg-white/5">
            <Download size={14}/> Esporta CSV
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Kpi label="Visitatori" value={k.unique_visitors} icon={Users}/>
        <Kpi label="Pageviews" value={k.page_views} icon={Eye}/>
        <Kpi label="Add to cart" value={k.add_to_cart} icon={ShoppingCart}/>
        <Kpi label="Ordini" value={k.orders} icon={PackageCheck} accent="text-emerald-300"/>
      </div>

      {/* Timeseries area chart */}
      <section className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
        <p className="label-eyebrow mb-4">Traffico nel tempo</p>
        {ts.length === 0 ? (
          <p className="text-sm text-zinc-500 py-10 text-center">Nessun dato ancora — apri il sito pubblico per generare eventi.</p>
        ) : (
          <div style={{ width: "100%", height: 300 }}>
            <ResponsiveContainer>
              <AreaChart data={ts} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="gVis" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.35}/>
                    <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="gPv" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={COLORS.secondary} stopOpacity={0.3}/>
                    <stop offset="95%" stopColor={COLORS.secondary} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid stroke={COLORS.grid} vertical={false}/>
                <XAxis dataKey="date" stroke={COLORS.axis} tick={{ fontSize: 10, fontFamily: "monospace" }} axisLine={false} tickLine={false}/>
                <YAxis stroke={COLORS.axis} tick={{ fontSize: 10, fontFamily: "monospace" }} axisLine={false} tickLine={false} allowDecimals={false}/>
                <Tooltip content={<ChartTooltip/>} cursor={{ stroke: "rgba(255,255,255,0.1)" }}/>
                <Legend wrapperStyle={{ fontSize: 11, fontFamily: "monospace", color: "#a1a1aa" }}/>
                <Area type="monotone" dataKey="visitors" name="Visitatori" stroke={COLORS.primary} strokeWidth={2} fill="url(#gVis)"/>
                <Area type="monotone" dataKey="pageviews" name="Pageviews" stroke={COLORS.secondary} strokeWidth={2} fill="url(#gPv)"/>
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Devices Pie */}
        <section className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
          <p className="label-eyebrow mb-3">Dispositivi</p>
          {deviceData.length === 0 ? <p className="text-sm text-zinc-500 py-8 text-center">Nessun dato.</p> : (
            <div style={{ width: "100%", height: 240 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={deviceData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                    innerRadius={55} outerRadius={90} paddingAngle={2}>
                    {deviceData.map((_, i) => <Cell key={i} fill={REFPIE[i % REFPIE.length]} stroke="#0B0B0D"/>)}
                  </Pie>
                  <Tooltip content={<ChartTooltip/>}/>
                  <Legend wrapperStyle={{ fontSize: 11, fontFamily: "monospace", color: "#a1a1aa" }}/>
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>

        {/* Referrers */}
        <section className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5 lg:col-span-2">
          <p className="label-eyebrow mb-3">Sorgenti di traffico (referrer)</p>
          {referrers.length === 0 ? <p className="text-sm text-zinc-500 py-8">Nessun referrer registrato.</p> : (
            <div style={{ width: "100%", height: 240 }}>
              <ResponsiveContainer>
                <BarChart data={referrers} margin={{ top: 5, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke={COLORS.grid} vertical={false}/>
                  <XAxis dataKey="host" stroke={COLORS.axis} tick={{ fontSize: 10, fontFamily: "monospace" }} axisLine={false} tickLine={false} interval={0} angle={-15} height={50}/>
                  <YAxis stroke={COLORS.axis} tick={{ fontSize: 10, fontFamily: "monospace" }} axisLine={false} tickLine={false} allowDecimals={false}/>
                  <Tooltip content={<ChartTooltip/>} cursor={{ fill: "rgba(255,255,255,0.03)" }}/>
                  <Bar dataKey="count" name="Visite" radius={[4, 4, 0, 0]}>
                    {referrers.map((_, i) => <Cell key={i} fill={REFPIE[i % REFPIE.length]}/>)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>
      </div>

      {/* Top pages & products */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
          <p className="label-eyebrow mb-3">Top pagine</p>
          {topPages.length === 0 ? <p className="text-sm text-zinc-500">Nessun dato.</p> :
            topPages.map(p => (
              <div key={p.path} className="flex justify-between border-b border-white/5 py-2 text-sm">
                <span className="text-zinc-300 truncate mr-3">{p.path}</span>
                <span className="font-mono text-white">{p.views}</span>
              </div>
            ))}
        </section>
        <section className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
          <p className="label-eyebrow mb-3">Top prodotti visti</p>
          {topProducts.length === 0 ? <p className="text-sm text-zinc-500">Nessun dato.</p> :
            topProducts.map(p => (
              <div key={p.slug} className="flex justify-between border-b border-white/5 py-2 text-sm">
                <span className="text-zinc-300 truncate mr-3">{p.slug}</span>
                <span className="font-mono text-white">{p.views}</span>
              </div>
            ))}
        </section>
      </div>

      <p className="text-xs text-zinc-600 font-mono">Fatturato periodo: {money(k.revenue_eur)}</p>
    </div>
  );
}
