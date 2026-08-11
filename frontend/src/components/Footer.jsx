import { Link } from "react-router-dom";
import { useLang } from "../lib/i18n";
import { resetConsent } from "../lib/privacy";

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
              <li><button type="button" onClick={resetConsent} className="text-zinc-400 hover:text-white transition-colors text-left">Preferenze cookie</button></li>
              <li><Link to="/legal/withdrawal" className="text-zinc-400 hover:text-white transition-colors">Diritto di recesso</Link></li>
              <li><Link to="/legal/delivery" className="text-zinc-400 hover:text-white transition-colors">Consegna digitale</Link></li>
              <li><Link to="/legal/refunds" className="text-zinc-400 hover:text-white transition-colors">Rimborsi</Link></li>
            </ul>
          </div>
        </div>

        {/* Business identity — required for GMC / EU consumer law */}
        <div className="border-t border-white/10 pt-6 pb-6 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-zinc-500">
          <div>
            <p className="label-eyebrow mb-2">Titolare</p>
            <p className="text-zinc-400">DIGITALSOFT DI MUNSHI SHIHAB</p>
            <p>P.IVA 04358941203 · REA 588058</p>
          </div>
          <div>
            <p className="label-eyebrow mb-2">Sede</p>
            <p>Via Aldo Pio Manuzio 24</p>
            <p>40132 Bologna (BO) · Italia</p>
          </div>
          <div>
            <p className="label-eyebrow mb-2">Contatti</p>
            <p><a href="mailto:supporto@licenzpol.it" className="text-zinc-400 hover:text-white">supporto@licenzpol.it</a></p>
            <p><a href="tel:+393936841051" className="text-zinc-400 hover:text-white">+39 393 684 1051</a></p>
          </div>
        </div>

        <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6 border-t border-white/10 pt-8">
          <p className="text-xs font-mono text-zinc-500 max-w-md">{t.footer.note}</p>
          <p className="text-xs font-mono text-zinc-600">© {new Date().getFullYear()} DIGITALSOFT DI MUNSHI SHIHAB · P.IVA 04358941203</p>
        </div>

        <div aria-hidden className="mt-12 select-none">
          <div className="font-display font-bold tracking-tighter leading-none text-white/[0.04]"
               style={{ fontSize: 'clamp(60px, 16vw, 260px)' }}>LicenzPøl</div>
        </div>
      </div>
    </footer>
  );
}
