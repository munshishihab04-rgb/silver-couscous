import { Link } from "react-router-dom";
import { useLang } from "../lib/i18n";

export default function Footer() {
  const { t } = useLang();
  return (
    <footer className="relative mt-32 border-t border-white/10 bg-black">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 pt-20 pb-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-10 mb-16">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded bg-white text-black flex items-center justify-center font-display font-bold text-[11px]">LP</div>
              <span className="font-display text-white text-base">Licenz<span className="text-zinc-500">Pøl</span></span>
            </div>
            <p className="text-sm text-zinc-500 leading-relaxed max-w-[220px]">{t.footer.tagline}</p>
          </div>
          <div>
            <p className="label-eyebrow mb-4">{t.footer.product}</p>
            <ul className="space-y-2 text-sm">
              <li><Link to="/catalog" className="text-zinc-400 hover:text-white transition-colors">{t.footer.catalog}</Link></li>
              <li><Link to="/compare" className="text-zinc-400 hover:text-white transition-colors">{t.footer.compare}</Link></li>
              <li><Link to="/support" className="text-zinc-400 hover:text-white transition-colors">{t.footer.support}</Link></li>
            </ul>
          </div>
          <div>
            <p className="label-eyebrow mb-4">{t.footer.company}</p>
            <ul className="space-y-2 text-sm">
              <li><Link to="/transparency" className="text-zinc-400 hover:text-white transition-colors">{t.footer.transparency}</Link></li>
              <li><Link to="/support" className="text-zinc-400 hover:text-white transition-colors">{t.footer.contact}</Link></li>
            </ul>
          </div>
          <div>
            <p className="label-eyebrow mb-4">{t.footer.legal}</p>
            <ul className="space-y-2 text-sm">
              <li><Link to="/legal/privacy" className="text-zinc-400 hover:text-white transition-colors">{t.footer.privacy}</Link></li>
              <li><Link to="/legal/terms" className="text-zinc-400 hover:text-white transition-colors">{t.footer.terms}</Link></li>
              <li><Link to="/legal/cookies" className="text-zinc-400 hover:text-white transition-colors">{t.footer.cookies}</Link></li>
            </ul>
          </div>
        </div>

        <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6 border-t border-white/10 pt-8">
          <p className="text-xs font-mono text-zinc-500 max-w-md">{t.footer.note}</p>
          <p className="text-xs font-mono text-zinc-600">© {new Date().getFullYear()} LicenzPol</p>
        </div>

        <div aria-hidden className="mt-12 select-none">
          <div className="font-display font-bold tracking-tighter leading-none text-white/[0.04]"
               style={{ fontSize: 'clamp(60px, 16vw, 260px)' }}>LicenzPøl</div>
        </div>
      </div>
    </footer>
  );
}
