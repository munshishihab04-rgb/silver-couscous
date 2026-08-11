import { useEffect, useState } from "react";
import { readConsent, saveConsent } from "../lib/privacy";

export default function CookieBanner() {
  const [consent, setConsent] = useState(() => readConsent());

  useEffect(() => {
    const update = (event) => setConsent(event.detail || readConsent());
    window.addEventListener("lp:consent", update);
    return () => window.removeEventListener("lp:consent", update);
  }, []);

  if (consent !== "pending") return null;

  const choose = (value) => {
    saveConsent(value);
    setConsent(value);
  };

  return (
    <div
      role="dialog"
      aria-label="Preferenze cookie"
      aria-modal="false"
      className="fixed z-[100] bottom-4 left-4 right-4 md:left-auto md:max-w-lg rounded-xl border border-white/15 bg-[#0B0B0D] p-5 shadow-2xl"
    >
      <h2 className="font-heading text-white text-lg">Preferenze cookie</h2>
      <p className="mt-2 text-sm leading-relaxed text-zinc-400">
        Usiamo solo cookie tecnici finché non scegli di consentire gli strumenti statistici. Puoi cambiare scelta dalla pagina Cookie.
      </p>
      <a href="/legal/cookies" className="mt-2 inline-block text-xs text-zinc-300 underline underline-offset-4">
        Leggi la Cookie policy
      </a>
      <div className="mt-4 flex flex-col-reverse sm:flex-row gap-2 sm:justify-end">
        <button onClick={() => choose("rejected")} className="pill-btn border border-white/20 text-white hover:bg-white/5">
          Rifiuta non essenziali
        </button>
        <button onClick={() => choose("accepted")} className="pill-btn bg-white text-black hover:bg-zinc-200">
          Accetta statistiche
        </button>
      </div>
    </div>
  );
}
