import { useEffect, useState } from "react";
import { adminApi, useAdminAuth } from "./auth.jsx";
import { toast } from "sonner";
import { Save, Loader2 } from "lucide-react";

export default function AdminPages() {
  const { token } = useAdminAuth();
  const api = adminApi(token);
  const [pages, setPages] = useState([]);
  const [current, setCurrent] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => { api.pages().then(list => { setPages(list); if (list.length) setCurrent(list[0]); }); /* eslint-disable-next-line */ }, []);

  const save = async () => {
    if (!current) return;
    setSaving(true);
    try {
      await api.updatePage(current.slug, {
        title_it: current.title_it, title_en: current.title_en,
        content_it: current.content_it, content_en: current.content_en,
      });
      toast.success("Pagina salvata");
    } catch { toast.error("Errore"); }
    finally { setSaving(false); }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr] gap-4" data-testid="admin-pages">
      <div>
        <div className="mb-4">
          <p className="label-eyebrow mb-2">CMS</p>
          <h1 className="font-display text-3xl tracking-tight">Pagine</h1>
        </div>
        <div className="rounded-xl border border-white/10 bg-[#0B0B0D] overflow-hidden">
          {pages.map(p => (
            <button key={p.slug} onClick={() => setCurrent(p)}
              data-testid={`admin-page-${p.slug}`}
              className={`w-full text-left px-4 py-3 border-b border-white/5 transition-colors ${current?.slug === p.slug ? "bg-white/[0.05]" : "hover:bg-white/[0.03]"}`}>
              <p className="text-white text-sm">{p.title_it}</p>
              <p className="text-xs font-mono text-zinc-500">/{p.slug}</p>
            </button>
          ))}
        </div>
      </div>

      {current && (
        <div className="rounded-xl border border-white/10 bg-[#0B0B0D] p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-2xl">/{current.slug}</h2>
            <button onClick={save} disabled={saving} data-testid="admin-page-save"
              className="pill-btn bg-white text-black hover:bg-zinc-200 disabled:opacity-50">
              {saving ? <Loader2 size={14} className="animate-spin"/> : <Save size={14}/>} Salva
            </button>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-1 block">Titolo IT</span>
              <input value={current.title_it} onChange={e => setCurrent({...current, title_it: e.target.value})}
                className="w-full bg-black border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none" />
            </label>
            <label className="block">
              <span className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-1 block">Title EN</span>
              <input value={current.title_en} onChange={e => setCurrent({...current, title_en: e.target.value})}
                className="w-full bg-black border border-white/10 rounded-md px-3 py-2 text-white focus:outline-none" />
            </label>
          </div>
          <label className="block">
            <span className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-1 block">Contenuto IT (Markdown)</span>
            <textarea value={current.content_it} onChange={e => setCurrent({...current, content_it: e.target.value})} rows={14}
              className="w-full bg-black border border-white/10 rounded-md px-3 py-2 text-white font-mono text-sm focus:outline-none" />
          </label>
          <label className="block">
            <span className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-1 block">Content EN (Markdown)</span>
            <textarea value={current.content_en} onChange={e => setCurrent({...current, content_en: e.target.value})} rows={14}
              className="w-full bg-black border border-white/10 rounded-md px-3 py-2 text-white font-mono text-sm focus:outline-none" />
          </label>
        </div>
      )}
    </div>
  );
}
