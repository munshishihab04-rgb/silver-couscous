import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAdminAuth } from "./auth.jsx";
import { toast } from "sonner";
import { Lock, Loader2 } from "lucide-react";

export default function AdminLogin() {
  const { login, user } = useAdminAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("admin@licenzpol.it");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) { nav("/admin", { replace: true }); return null; }

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await login(email, password);
      toast.success("Benvenuto");
      nav("/admin");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      toast.error(typeof detail === "string" ? detail : "Errore di accesso");
    } finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-2 mb-8 justify-center">
          <div className="w-8 h-8 rounded-md bg-white text-black flex items-center justify-center font-display font-bold">LP</div>
          <p className="font-display text-xl">Licenz<span className="text-zinc-500">Pøl</span></p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-[#0B0B0D] p-8 relative overflow-hidden">
          <div className="absolute inset-0 grain" />
          <div className="relative">
            <p className="label-eyebrow mb-2">Admin</p>
            <h1 className="font-display text-3xl tracking-tight">Accedi al pannello</h1>
            <p className="text-sm text-zinc-500 mt-1">Riservato al team di LicenzPol.</p>

            <form onSubmit={submit} className="mt-6 space-y-4">
              <label className="block">
                <span className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-1 block">Email</span>
                <input data-testid="admin-login-email" type="email" required value={email} onChange={e => setEmail(e.target.value)}
                  className="w-full bg-black border border-white/10 rounded-md px-3 py-2.5 text-white focus:outline-none focus:border-white/30" />
              </label>
              <label className="block">
                <span className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-1 block">Password</span>
                <input data-testid="admin-login-password" type="password" required value={password} onChange={e => setPassword(e.target.value)}
                  className="w-full bg-black border border-white/10 rounded-md px-3 py-2.5 text-white focus:outline-none focus:border-white/30" />
              </label>
              <button data-testid="admin-login-submit" type="submit" disabled={busy}
                className="pill-btn bg-white text-black hover:bg-zinc-200 w-full disabled:opacity-50">
                {busy ? <Loader2 size={16} className="animate-spin"/> : <Lock size={16} />}
                {busy ? "Accesso…" : "Accedi"}
              </button>
            </form>
          </div>
        </div>
        <p className="text-center text-xs font-mono text-zinc-600 mt-6">Sessione JWT · 24 ore</p>
      </div>
    </div>
  );
}
