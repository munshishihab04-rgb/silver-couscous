import { useEffect, useState } from "react";
import { adminApi, useAdminAuth } from "./auth.jsx";
import { Users, Eye, ShoppingCart, PackageCheck } from "lucide-react";

const money = (n) => new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(n || 0);

const Kpi = ({ label, value, icon: Icon }) => (
  <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-4">
    <div className="flex items-center justify-between text-zinc-400 mb-2">
      <span className="label-eyebrow">{label}</span><Icon size={14}/>
    </div>
    <p className="font-display text-2xl md:text-3xl">{value}</p>
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
  const maxVisitors = Math.max(1, ...d.timeseries.map(t => t.visitors || 0));

  return (
    <div className="space-y-8" data-testid="admin-analytics-page">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <p className="label-eyebrow mb-2">Analytics</p>
          <h1 className="font-display text-3xl md:text-4xl tracking-tight">Comportamento visitatori</h1>
          <p className="text-sm text-zinc-500 mt-1">Dati raccolti dal tracker interno di LicenzPol.</p>
        </div>
        <div className="flex gap-2">
          {["24h", "7d", "30d", "90d"].map(r => (
            <button key={r} onClick={() => setRange(r)}
              className={`chip ${range === r ? "!bg-white !text-black !border-white" : ""}`}>{r}</button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Kpi label="Visitatori" value={k.unique_visitors} icon={Users}/>
        <Kpi label="Pageviews" value={k.page_views} icon={Eye}/>
        <Kpi label="Add to cart" value={k.add_to_cart} icon={ShoppingCart}/>
        <Kpi label="Ordini" value={k.orders} icon={PackageCheck}/>
      </div>

      {/* Timeseries visitors bar chart */}
      <section className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
        <p className="label-eyebrow mb-4">Visitatori giornalieri</p>
        {d.timeseries.length === 0 ? (
          <p className="text-sm text-zinc-500">Nessun dato ancora — apri il sito pubblico per generare eventi.</p>
        ) : (
          <div className="flex items-end gap-1 h-40">
            {d.timeseries.map(t => {
              const h = Math.max(6, Math.round((t.visitors / maxVisitors) * 140));
              return (
                <div key={t.date} className="flex-1 flex flex-col items-center gap-1 group">
                  <div className="w-full bg-white/20 group-hover:bg-white transition-colors rounded-sm" style={{ height: h }} title={`${t.date}: ${t.visitors} visitatori`} />
                  <span className="text-[9px] font-mono text-zinc-600 rotate-0">{t.date.slice(5)}</span>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
          <p className="label-eyebrow mb-3">Referrer</p>
          {d.referrers.length === 0 ? <p className="text-sm text-zinc-500">Nessun referrer.</p> :
            d.referrers.map(r => (
              <div key={r.host} className="flex justify-between border-b border-white/5 py-2 text-sm">
                <span className="text-zinc-300 truncate">{r.host}</span>
                <span className="font-mono text-white">{r.count}</span>
              </div>
            ))}
        </section>
        <section className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
          <p className="label-eyebrow mb-3">Dispositivi</p>
          {Object.entries(d.devices).map(([k, v]) => (
            <div key={k} className="flex justify-between border-b border-white/5 py-2 text-sm">
              <span className="text-zinc-300 capitalize">{k}</span>
              <span className="font-mono text-white">{v}</span>
            </div>
          ))}
        </section>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
          <p className="label-eyebrow mb-3">Top pagine</p>
          {d.top_pages.length === 0 ? <p className="text-sm text-zinc-500">Nessun dato.</p> :
            d.top_pages.map(p => (
              <div key={p.path} className="flex justify-between border-b border-white/5 py-2 text-sm">
                <span className="text-zinc-300 truncate mr-3">{p.path}</span>
                <span className="font-mono text-white">{p.views}</span>
              </div>
            ))}
        </section>
        <section className="rounded-xl border border-white/10 bg-[#0B0B0D] p-5">
          <p className="label-eyebrow mb-3">Top prodotti visti</p>
          {d.top_products.length === 0 ? <p className="text-sm text-zinc-500">Nessun dato.</p> :
            d.top_products.map(p => (
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
