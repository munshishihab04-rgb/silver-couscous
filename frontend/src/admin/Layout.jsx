import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAdminAuth } from "./auth.jsx";
import {
  LayoutDashboard, Package, Users, LifeBuoy, FileText, Settings,
  BarChart3, LogOut, Menu, X, ExternalLink, ShieldCheck, ShoppingBag,
  Award,
} from "lucide-react";

const items = [
  { to: "/admin", end: true, label: "Dashboard", icon: LayoutDashboard },
  { to: "/admin/orders", label: "Ordini", icon: ShoppingBag },
  { to: "/admin/merchant", label: "Merchant", icon: Award },
  { to: "/admin/products", label: "Prodotti", icon: Package },
  { to: "/admin/customers", label: "Clienti", icon: Users },
  { to: "/admin/tickets", label: "Ticket", icon: LifeBuoy },
  { to: "/admin/pages", label: "Pagine", icon: FileText },
  { to: "/admin/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/admin/settings", label: "Impostazioni", icon: Settings },
];

export default function AdminLayout() {
  const { user, loading, logout } = useAdminAuth();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);

  useEffect(() => { if (!loading && !user) nav("/admin/login", { replace: true }); }, [loading, user, nav]);

  if (loading) return <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center">…</div>;
  if (!user) return null;

  const Sidebar = ({ onNav }) => (
    <nav className="flex flex-col gap-1 p-4 h-full" data-testid="admin-sidebar">
      <div className="flex items-center gap-2 mb-6 px-2">
        <div className="w-7 h-7 rounded-md bg-white text-black flex items-center justify-center font-display font-bold text-[13px]">LP</div>
        <div>
          <p className="font-display text-white text-sm leading-none">Licenz<span className="text-zinc-500">Pøl</span></p>
          <p className="text-[10px] font-mono uppercase tracking-widest text-zinc-500 mt-0.5">Admin</p>
        </div>
      </div>
      {items.map(it => (
        <NavLink key={it.to} to={it.to} end={it.end} onClick={onNav}
          data-testid={`admin-nav-${it.label.toLowerCase()}`}
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-heading transition-colors ${
              isActive ? "bg-white/[0.08] text-white" : "text-zinc-400 hover:text-white hover:bg-white/[0.04]"
            }`
          }>
          <it.icon size={16} /> {it.label}
        </NavLink>
      ))}
      <div className="mt-auto pt-4 border-t border-white/10 space-y-1">
        <a href="/" target="_blank" rel="noreferrer" className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-heading text-zinc-400 hover:text-white hover:bg-white/[0.04] transition-colors">
          <ExternalLink size={16}/> Sito pubblico
        </a>
        <button onClick={() => { logout(); nav("/admin/login"); }} data-testid="admin-logout"
          className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm font-heading text-zinc-400 hover:text-red-300 hover:bg-red-500/10 transition-colors">
          <LogOut size={16}/> Esci
        </button>
        <div className="px-3 pt-3 text-[10px] font-mono uppercase tracking-widest text-zinc-600">
          <span className="inline-flex items-center gap-1"><ShieldCheck size={11}/> {user.email}</span>
        </div>
      </div>
    </nav>
  );

  return (
    <div className="min-h-screen bg-[#050505] text-white flex">
      {/* Desktop sidebar */}
      <aside className="hidden md:block w-60 border-r border-white/10 bg-[#0A0A0C] shrink-0 sticky top-0 h-screen">
        <Sidebar />
      </aside>

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 inset-x-0 z-40 h-14 border-b border-white/10 bg-black/80 backdrop-blur flex items-center justify-between px-4">
        <button onClick={() => setOpen(true)} data-testid="admin-mobile-menu"><Menu size={22} /></button>
        <p className="font-display text-sm">Licenz<span className="text-zinc-500">Pøl</span> Admin</p>
        <button onClick={() => { logout(); nav("/admin/login"); }} className="text-zinc-400"><LogOut size={18} /></button>
      </div>
      {open && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="w-64 bg-[#0A0A0C] h-full border-r border-white/10">
            <div className="flex justify-end p-4"><button onClick={() => setOpen(false)}><X size={20} /></button></div>
            <Sidebar onNav={() => setOpen(false)} />
          </div>
          <div className="flex-1 bg-black/70" onClick={() => setOpen(false)} />
        </div>
      )}

      <main className="flex-1 pt-14 md:pt-0 min-w-0">
        <div className="max-w-6xl mx-auto px-4 md:px-8 py-8 md:py-10">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
