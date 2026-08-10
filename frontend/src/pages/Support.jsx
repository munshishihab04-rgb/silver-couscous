import { useState } from "react";
import { useLang } from "../lib/i18n";
import { api } from "../lib/api";
import { toast } from "sonner";
import { Mail, MessageSquare, Clock } from "lucide-react";

export default function Support() {
  const { lang, t } = useLang();
  const [form, setForm] = useState({ email: "", subject: "", message: "" });
  const [sending, setSending] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setSending(true);
    try {
      await api.support({ ...form, language: lang });
      toast.success(t.support.sent);
      setForm({ email: "", subject: "", message: "" });
    } catch { toast.error("Error"); }
    finally { setSending(false); }
  };

  return (
    <div className="max-w-[1200px] mx-auto px-6 md:px-10 py-16" data-testid="support-page">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
        <div>
          <p className="label-eyebrow mb-3">Support</p>
          <h1 className="font-display text-4xl md:text-5xl tracking-tight">{t.support.title}</h1>
          <p className="text-zinc-400 mt-4 leading-relaxed max-w-md">{t.support.sub}</p>
          <div className="mt-10 space-y-6">
            {[
              { i: Mail, t: t.support.email, v: "support@licenzpol.example" },
              { i: MessageSquare, t: "Live chat", v: lang === "it" ? "Non ancora attiva — in arrivo" : "Not active yet — coming soon" },
              { i: Clock, t: lang === "it" ? "Orari" : "Hours", v: lang === "it" ? "Lun-Ven, 9-18 (CET)" : "Mon-Fri, 9-18 (CET)" },
            ].map((it, i) => {
              const Icon = it.i;
              return (
                <div key={i} className="flex items-start gap-4 pb-6 border-b border-white/5">
                  <Icon size={20} className="text-zinc-500 mt-0.5" />
                  <div><p className="label-eyebrow mb-1">{it.t}</p><p className="text-white">{it.v}</p></div>
                </div>
              );
            })}
          </div>
        </div>

        <form onSubmit={submit} className="rounded-xl border border-white/10 bg-[#0B0B0D] p-6 md:p-8 space-y-4">
          {[["email", t.support.email, "email"], ["subject", t.support.subject, "text"]].map(([k, l, t2]) => (
            <label key={k} className="block">
              <span className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-1 block">{l}</span>
              <input data-testid={`support-${k}`} required type={t2} value={form[k]} onChange={e => setForm({ ...form, [k]: e.target.value })}
                className="w-full bg-black border border-white/10 rounded-md px-3 py-2.5 text-white focus:outline-none focus:border-white/30" />
            </label>
          ))}
          <label className="block">
            <span className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-1 block">{t.support.message}</span>
            <textarea data-testid="support-message" required rows={6} value={form.message} onChange={e => setForm({ ...form, message: e.target.value })}
              className="w-full bg-black border border-white/10 rounded-md px-3 py-2.5 text-white focus:outline-none focus:border-white/30" />
          </label>
          <button data-testid="support-send" disabled={sending} className="pill-btn bg-white text-black hover:bg-zinc-200 w-full disabled:opacity-50">
            {sending ? "..." : t.support.send}
          </button>
        </form>
      </div>
    </div>
  );
}
