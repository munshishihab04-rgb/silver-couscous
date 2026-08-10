import { useEffect, useMemo, useState } from "react";
import { adminApi, useAdminAuth } from "./auth.jsx";
import { toast } from "sonner";
import { Search, Plus, Trash2, Edit3, X, Save, Loader2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../components/ui/dialog";

const money = (n) => new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(n || 0);

const CATS = [
  { key: "os", label: "Sistemi Operativi" }, { key: "office", label: "Office" },
  { key: "security", label: "Sicurezza" }, { key: "creative", label: "Creativo" },
  { key: "cad", label: "CAD" }, { key: "business", label: "Business" }, { key: "utility", label: "Utility" },
];

const emptyProduct = () => ({
  slug: "", name: "", category: "office", brand: "", mark: "",
  colorKey: "work", image_url: "", platforms: ["Windows"], licenseType: "Perpetua",
  tagline_it: "", tagline_en: "", description_it: "", description_en: "",
  features_it: [], features_en: [], compatibility_it: "", compatibility_en: "",
  whatYouGet_it: [], whatYouGet_en: [], activation_it: [], activation_en: [],
  variants: [{ id: "v1", edition: "Standard", duration_months: 0, devices: 1, price_eur: 0, list_price_eur: null }],
  faq: [],
});

export default function AdminProducts() {
  const { token } = useAdminAuth();
  const api = adminApi(token);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);      // product object or "new"
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const r = await api.products({ q: q || undefined, category: category || undefined, limit: 200 });
      setItems(r.items); setTotal(r.total);
    } finally { setLoading(false); }
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [q, category]);

  const openNew = () => setEditing({ mode: "new", data: emptyProduct() });
  const openEdit = async (slug) => {
    const p = await api.product(slug);
    setEditing({ mode: "edit", data: p });
  };

  const del = async (slug) => {
    if (!window.confirm(`Eliminare ${slug}?`)) return;
    try { await api.deleteProduct(slug); toast.success("Prodotto eliminato"); load(); }
    catch { toast.error("Errore"); }
  };

  const save = async () => {
    if (!editing) return;
    setSaving(true);
    try {
      if (editing.mode === "new") {
        if (!editing.data.slug || !editing.data.name) { toast.error("Slug e nome obbligatori"); setSaving(false); return; }
        await api.createProduct(editing.data);
        toast.success("Prodotto creato");
      } else {
        const { slug, ...rest } = editing.data;
        await api.updateProduct(slug, rest);
        toast.success("Salvato");
      }
      setEditing(null); load();
    } catch (e) { toast.error(e?.response?.data?.detail || "Errore"); }
    finally { setSaving(false); }
  };

  return (
    <div className="space-y-6" data-testid="admin-products-page">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <p className="label-eyebrow mb-2">Catalog</p>
          <h1 className="font-display text-3xl md:text-4xl tracking-tight">Prodotti</h1>
          <p className="text-sm text-zinc-500 mt-1">{total} prodotti in MongoDB.</p>
        </div>
        <button data-testid="admin-product-new" onClick={openNew} className="pill-btn bg-white text-black hover:bg-zinc-200">
          <Plus size={16}/> Nuovo prodotto
        </button>
      </div>

      <div className="flex flex-col sm:flex-row gap-2">
        <div className="flex-1 flex items-center gap-2 bg-[#0B0B0D] border border-white/10 rounded-full px-3 py-2">
          <Search size={16} className="text-zinc-500" />
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Cerca per nome, brand o slug…"
            data-testid="admin-products-search"
            className="bg-transparent w-full text-sm text-white placeholder:text-zinc-500 focus:outline-none" />
        </div>
        <select value={category} onChange={e => setCategory(e.target.value)}
          className="bg-[#0B0B0D] border border-white/10 rounded-full px-4 py-2 text-sm text-white focus:outline-none">
          <option value="">Tutte le categorie</option>
          {CATS.map(c => <option key={c.key} value={c.key}>{c.label}</option>)}
        </select>
      </div>

      <div className="rounded-xl border border-white/10 bg-[#0B0B0D] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-sm">
            <thead className="bg-white/[0.03] text-zinc-400 text-xs font-mono uppercase tracking-widest">
              <tr>
                <th className="text-left px-4 py-3">Prodotto</th>
                <th className="text-left px-4 py-3">Brand</th>
                <th className="text-left px-4 py-3">Cat.</th>
                <th className="text-right px-4 py-3">Prezzo</th>
                <th className="text-right px-4 py-3 w-32"></th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="text-center py-8 text-zinc-500">Caricamento…</td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={5} className="text-center py-8 text-zinc-500">Nessun prodotto.</td></tr>
              ) : items.map(p => (
                <tr key={p.slug} className="border-t border-white/5 hover:bg-white/[0.02]">
                  <td className="px-4 py-3">
                    <p className="text-white leading-tight">{p.name}</p>
                    <p className="text-xs font-mono text-zinc-500 mt-0.5">{p.slug}</p>
                  </td>
                  <td className="px-4 py-3 text-zinc-300">{p.brand}</td>
                  <td className="px-4 py-3"><span className="chip !py-0.5 !text-[10px]">{p.category}</span></td>
                  <td className="px-4 py-3 text-right font-mono text-white">{money(p.variants?.[0]?.price_eur)}</td>
                  <td className="px-4 py-3 text-right space-x-1">
                    <button onClick={() => openEdit(p.slug)} data-testid={`admin-product-edit-${p.slug}`}
                      className="p-2 rounded-md border border-white/10 hover:bg-white/5 text-zinc-300 hover:text-white transition-colors">
                      <Edit3 size={13}/>
                    </button>
                    <button onClick={() => del(p.slug)} data-testid={`admin-product-delete-${p.slug}`}
                      className="p-2 rounded-md border border-white/10 hover:bg-red-500/10 hover:border-red-500/30 text-zinc-300 hover:text-red-300 transition-colors">
                      <Trash2 size={13}/>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Edit dialog */}
      <Dialog open={!!editing} onOpenChange={(o) => !o && setEditing(null)}>
        <DialogContent className="max-w-2xl bg-[#0A0A0C] text-white border border-white/10 p-0 max-h-[90vh] flex flex-col">
          <DialogHeader className="px-6 pt-6 pb-4 border-b border-white/10 shrink-0">
            <DialogTitle className="font-display text-xl">
              {editing?.mode === "new" ? "Nuovo prodotto" : editing?.data?.name}
            </DialogTitle>
          </DialogHeader>
          {editing && (
            <div className="overflow-y-auto p-6 space-y-4">
              {editing.mode === "new" && (
                <Field label="Slug (URL)" value={editing.data.slug}
                  onChange={v => setEditing({...editing, data: {...editing.data, slug: v.toLowerCase().replace(/[^a-z0-9-]/g, '-')}})} />
              )}
              <Field label="Nome" value={editing.data.name} onChange={v => setEditing({...editing, data: {...editing.data, name: v}})} testid="edit-name" />
              <div className="grid grid-cols-2 gap-3">
                <Field label="Brand" value={editing.data.brand} onChange={v => setEditing({...editing, data: {...editing.data, brand: v}})} />
                <Field label="Sigla (mark)" value={editing.data.mark} onChange={v => setEditing({...editing, data: {...editing.data, mark: v}})} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <SelectField label="Categoria" value={editing.data.category} onChange={v => setEditing({...editing, data: {...editing.data, category: v}})}
                  options={CATS.map(c => [c.key, c.label])} />
                <SelectField label="Tipo licenza" value={editing.data.licenseType} onChange={v => setEditing({...editing, data: {...editing.data, licenseType: v}})}
                  options={[["Perpetua","Perpetua"], ["Abbonamento","Abbonamento"]]} />
              </div>
              <Field label="Immagine (URL)" value={editing.data.image_url || ""} onChange={v => setEditing({...editing, data: {...editing.data, image_url: v}})} />
              <div className="grid grid-cols-2 gap-3">
                <Field label="Tagline IT" value={editing.data.tagline_it} onChange={v => setEditing({...editing, data: {...editing.data, tagline_it: v}})} />
                <Field label="Tagline EN" value={editing.data.tagline_en} onChange={v => setEditing({...editing, data: {...editing.data, tagline_en: v}})} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <TextareaField label="Descrizione IT" value={editing.data.description_it} onChange={v => setEditing({...editing, data: {...editing.data, description_it: v}})} />
                <TextareaField label="Descrizione EN" value={editing.data.description_en} onChange={v => setEditing({...editing, data: {...editing.data, description_en: v}})} />
              </div>
              <VariantsEditor variants={editing.data.variants || []}
                onChange={v => setEditing({...editing, data: {...editing.data, variants: v}})} />
            </div>
          )}
          <div className="border-t border-white/10 p-4 flex items-center justify-end gap-2 shrink-0">
            <button onClick={() => setEditing(null)} className="pill-btn border border-white/20 text-white hover:bg-white/5"><X size={14}/> Annulla</button>
            <button onClick={save} disabled={saving} data-testid="admin-product-save"
              className="pill-btn bg-white text-black hover:bg-zinc-200 disabled:opacity-50">
              {saving ? <Loader2 size={14} className="animate-spin"/> : <Save size={14}/>}
              {saving ? "Salvo…" : "Salva"}
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

const Field = ({ label, value, onChange, testid }) => (
  <label className="block">
    <span className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-1 block">{label}</span>
    <input data-testid={testid} value={value ?? ""} onChange={e => onChange(e.target.value)}
      className="w-full bg-black border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none focus:border-white/30" />
  </label>
);
const TextareaField = ({ label, value, onChange }) => (
  <label className="block">
    <span className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-1 block">{label}</span>
    <textarea value={value ?? ""} onChange={e => onChange(e.target.value)} rows={3}
      className="w-full bg-black border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none focus:border-white/30" />
  </label>
);
const SelectField = ({ label, value, onChange, options }) => (
  <label className="block">
    <span className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-1 block">{label}</span>
    <select value={value ?? ""} onChange={e => onChange(e.target.value)}
      className="w-full bg-black border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none focus:border-white/30">
      {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
    </select>
  </label>
);

const VariantsEditor = ({ variants, onChange }) => {
  const upd = (i, k, v) => { const n = [...variants]; n[i] = { ...n[i], [k]: v }; onChange(n); };
  const add = () => onChange([...(variants || []), { id: `v${(variants?.length || 0) + 1}`, edition: "Standard", duration_months: 0, devices: 1, price_eur: 0 }]);
  const rm = (i) => onChange(variants.filter((_, idx) => idx !== i));
  return (
    <div>
      <p className="label-eyebrow mb-2">Varianti</p>
      <div className="space-y-2">
        {variants.map((v, i) => (
          <div key={i} className="grid grid-cols-6 gap-2 items-end border border-white/10 rounded-md p-2">
            <label className="col-span-2 block">
              <span className="text-[10px] font-mono uppercase text-zinc-500 block mb-0.5">Edizione</span>
              <input value={v.edition} onChange={e => upd(i, "edition", e.target.value)}
                className="w-full bg-black border border-white/10 rounded px-2 py-1.5 text-white text-xs focus:outline-none" />
            </label>
            <label className="block">
              <span className="text-[10px] font-mono uppercase text-zinc-500 block mb-0.5">Mesi</span>
              <input type="number" value={v.duration_months ?? 0} onChange={e => upd(i, "duration_months", parseInt(e.target.value) || 0)}
                className="w-full bg-black border border-white/10 rounded px-2 py-1.5 text-white text-xs focus:outline-none" />
            </label>
            <label className="block">
              <span className="text-[10px] font-mono uppercase text-zinc-500 block mb-0.5">Dispositivi</span>
              <input type="number" value={v.devices ?? 1} onChange={e => upd(i, "devices", parseInt(e.target.value) || 1)}
                className="w-full bg-black border border-white/10 rounded px-2 py-1.5 text-white text-xs focus:outline-none" />
            </label>
            <label className="block">
              <span className="text-[10px] font-mono uppercase text-zinc-500 block mb-0.5">Prezzo €</span>
              <input type="number" step="0.01" value={v.price_eur ?? 0} onChange={e => upd(i, "price_eur", parseFloat(e.target.value) || 0)}
                className="w-full bg-black border border-white/10 rounded px-2 py-1.5 text-white text-xs focus:outline-none" />
            </label>
            <button onClick={() => rm(i)} className="text-zinc-400 hover:text-red-400 justify-self-end p-1"><Trash2 size={13}/></button>
          </div>
        ))}
      </div>
      <button onClick={add} className="mt-2 text-xs font-mono text-zinc-400 hover:text-white transition-colors">+ Aggiungi variante</button>
    </div>
  );
};
