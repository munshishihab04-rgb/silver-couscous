import { useEffect, useState } from "react";
import { adminApi, useAdminAuth } from "./auth.jsx";
import { toast } from "sonner";
import { Save, Loader2, Plus, Trash2 } from "lucide-react";

const Field = ({ label, hint, value, onChange, mono, testid, type = "text" }) => (
  <label className="block">
    <div className="flex items-baseline justify-between mb-1">
      <span className="text-xs font-mono uppercase tracking-widest text-zinc-500">{label}</span>
      {hint && <span className="text-[10px] text-zinc-600">{hint}</span>}
    </div>
    <input data-testid={testid} type={type} value={value ?? ""} onChange={e => onChange(e.target.value)}
      className={`w-full bg-black border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none focus:border-white/30 ${mono ? "font-mono text-sm" : ""}`} />
  </label>
);

const AreaField = ({ label, hint, value, onChange, testid }) => (
  <label className="block">
    <div className="flex items-baseline justify-between mb-1">
      <span className="text-xs font-mono uppercase tracking-widest text-zinc-500">{label}</span>
      {hint && <span className="text-[10px] text-zinc-600">{hint}</span>}
    </div>
    <textarea data-testid={testid} value={value ?? ""} onChange={e => onChange(e.target.value)} rows={4}
      className="w-full bg-black border border-white/10 rounded-md px-3 py-2 text-white font-mono text-xs focus:outline-none focus:border-white/30" />
  </label>
);

export default function AdminSettings() {
  const { token, user } = useAdminAuth();
  const api = adminApi(token);
  const [s, setS] = useState(null);
  const [saving, setSaving] = useState(false);
  const [admins, setAdmins] = useState([]);
  const [newAdmin, setNewAdmin] = useState({ email: "", password: "", name: "" });

  useEffect(() => {
    api.settings().then(setS);
    api.admins().then(setAdmins);
    // eslint-disable-next-line
  }, []);

  const set = (k, v) => setS(prev => ({ ...prev, [k]: v }));

  const save = async () => {
    setSaving(true);
    try { const r = await api.updateSettings(s); setS(r); toast.success("Impostazioni salvate"); }
    catch { toast.error("Errore"); }
    finally { setSaving(false); }
  };

  const addAdmin = async () => {
    if (!newAdmin.email || !newAdmin.password) { toast.error("Email e password"); return; }
    try {
      await api.createAdmin(newAdmin);
      setNewAdmin({ email: "", password: "", name: "" });
      const list = await api.admins(); setAdmins(list);
      toast.success("Admin creato");
    } catch (e) { toast.error(e?.response?.data?.detail || "Errore"); }
  };

  const delAdmin = async (id) => {
    if (!window.confirm("Eliminare questo admin?")) return;
    try { await api.deleteAdmin(id); setAdmins(await api.admins()); toast.success("Rimosso"); }
    catch (e) { toast.error(e?.response?.data?.detail || "Errore"); }
  };

  if (!s) return <div className="text-zinc-500">Caricamento…</div>;

  return (
    <div className="space-y-8" data-testid="admin-settings-page">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <p className="label-eyebrow mb-2">Site</p>
          <h1 className="font-display text-3xl md:text-4xl tracking-tight">Impostazioni</h1>
        </div>
        <button onClick={save} disabled={saving} data-testid="admin-settings-save"
          className="pill-btn bg-white text-black hover:bg-zinc-200 disabled:opacity-50">
          {saving ? <Loader2 size={14} className="animate-spin"/> : <Save size={14}/>} Salva
        </button>
      </div>

      {/* Brand */}
      <Section title="Brand & Logo">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Logo testo" value={s.logo_text} onChange={v => set("logo_text", v)} testid="setting-logo-text" />
          <Field label="Logo immagine (URL)" hint="lascia vuoto per usare il testo" value={s.logo_url} onChange={v => set("logo_url", v)} testid="setting-logo-url" />
          <Field label="Site title" value={s.site_title} onChange={v => set("site_title", v)} testid="setting-title" />
          <Field label="Email di contatto pubblica" value={s.primary_email} onChange={v => set("primary_email", v)} />
        </div>
        <AreaField label="Meta description (SEO)" hint="max ~160 caratteri" value={s.site_description} onChange={v => set("site_description", v)} testid="setting-description" />
      </Section>

      {/* Tracking */}
      <Section title="Tracking & Analytics">
        <p className="text-sm text-zinc-500">Incolla qui gli ID delle piattaforme. Vengono iniettati automaticamente nel sito pubblico.</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Field label="GA4 Measurement ID" hint="G-XXXXXXX" mono value={s.ga4_measurement_id} onChange={v => set("ga4_measurement_id", v)} testid="setting-ga4" />
          <Field label="Google Tag Manager" hint="GTM-XXXXX" mono value={s.gtm_container_id} onChange={v => set("gtm_container_id", v)} testid="setting-gtm" />
          <Field label="Meta Pixel ID" mono value={s.meta_pixel_id} onChange={v => set("meta_pixel_id", v)} testid="setting-meta-pixel" />
        </div>
        <AreaField label="HTML custom nel <head>" hint="script/verifiche" value={s.custom_head_html} onChange={v => set("custom_head_html", v)} testid="setting-head-html" />
        <AreaField label="HTML custom in fondo al <body>" hint="chat, live agent, pixel manuali" value={s.custom_body_html} onChange={v => set("custom_body_html", v)} testid="setting-body-html" />
      </Section>

      {/* Admins */}
      <Section title="Utenti admin">
        <div className="rounded-md border border-white/10 divide-y divide-white/5">
          {admins.map(a => (
            <div key={a.id} className="flex items-center justify-between px-4 py-3">
              <div>
                <p className="text-white text-sm">{a.email}</p>
                <p className="text-xs font-mono text-zinc-500">{a.name} · {a.role}</p>
              </div>
              {a.email !== user.email && (
                <button onClick={() => delAdmin(a.id)} className="p-2 rounded-md border border-white/10 hover:bg-red-500/10 text-zinc-400 hover:text-red-300 transition-colors">
                  <Trash2 size={13}/>
                </button>
              )}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end mt-3">
          <Field label="Nuovo admin email" value={newAdmin.email} onChange={v => setNewAdmin({...newAdmin, email: v})} />
          <Field label="Password" type="password" value={newAdmin.password} onChange={v => setNewAdmin({...newAdmin, password: v})} />
          <button onClick={addAdmin} data-testid="admin-add-user"
            className="pill-btn border border-white/20 text-white hover:bg-white/5"><Plus size={14}/> Aggiungi</button>
        </div>
      </Section>
    </div>
  );
}

const Section = ({ title, children }) => (
  <section className="rounded-xl border border-white/10 bg-[#0B0B0D] p-6 space-y-4">
    <h2 className="font-display text-xl">{title}</h2>
    {children}
  </section>
);
