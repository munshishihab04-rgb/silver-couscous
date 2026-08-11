import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { CheckCircle2, Clock, XCircle, Mail } from "lucide-react";
import { useLang } from "../lib/i18n";

const STATUS_COPY = {
  paid: {
    icon: CheckCircle2, color: "text-emerald-400",
    title_it: "Pagamento completato",
    title_en: "Payment complete",
    body_it: "Grazie! Il pagamento è stato ricevuto correttamente. La chiave di licenza verrà inviata via email entro pochi minuti.",
    body_en: "Thank you! Payment received. Your license key will be delivered via email within minutes.",
  },
  fulfilled: {
    icon: CheckCircle2, color: "text-emerald-400",
    title_it: "Licenza consegnata",
    title_en: "License delivered",
    body_it: "La chiave è stata inviata all'indirizzo email indicato. Controlla anche la cartella spam.",
    body_en: "The key has been sent to the email you provided. Check the spam folder just in case.",
  },
  fulfillment_pending: {
    icon: Mail, color: "text-yellow-300",
    title_it: "Pagamento ricevuto — consegna in corso",
    title_en: "Payment received — delivery in progress",
    body_it: "Il pagamento è andato a buon fine. Stiamo processando la consegna della licenza: riceverai un'email a breve.",
    body_en: "Payment received. We are processing your license delivery; you'll receive an email shortly.",
  },
  pending_payment: {
    icon: Clock, color: "text-yellow-300",
    title_it: "In attesa di conferma",
    title_en: "Awaiting confirmation",
    body_it: "Il pagamento è ancora in elaborazione. Aggiorna la pagina tra qualche istante o attendi l'email.",
    body_en: "Payment is still processing. Refresh in a few moments or wait for the confirmation email.",
  },
  failed: {
    icon: XCircle, color: "text-red-400",
    title_it: "Pagamento non riuscito",
    title_en: "Payment failed",
    body_it: "Il tuo pagamento non è andato a buon fine. Non è stato addebitato nulla. Riprova o contatta l'assistenza.",
    body_en: "Your payment did not go through. Nothing was charged. Try again or contact support.",
  },
  cancelled: {
    icon: XCircle, color: "text-zinc-400",
    title_it: "Pagamento annullato",
    title_en: "Payment cancelled",
    body_it: "Hai annullato il pagamento. Puoi riprovare quando vuoi.",
    body_en: "You cancelled the payment. You can try again anytime.",
  },
};

export function CheckoutResult() {
  const { orderId } = useParams();
  const { lang } = useLang();
  const [state, setState] = useState({ status: "pending_payment", loading: true });

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      const token = sessionStorage.getItem(`licenzpol_order_token_${orderId}`) || "";
      fetch(`${process.env.REACT_APP_BACKEND_URL}/api/payments/status/${orderId}`, {
        headers: { "X-Order-Token": token },
      })
        .then(r => r.json())
        .then(d => { if (!cancelled) setState({ ...d, loading: false }); })
        .catch(() => { if (!cancelled) setState({ status: "pending_payment", loading: false }); });
    };
    load();
    const iv = setInterval(load, 5000); // poll every 5s
    return () => { cancelled = true; clearInterval(iv); };
  }, [orderId]);

  const status = state.status || "pending_payment";
  const copy = STATUS_COPY[status] || STATUS_COPY.pending_payment;
  const Icon = copy.icon;
  const isFinal = ["fulfilled", "failed", "cancelled"].includes(status);

  return (
    <div className="max-w-[720px] mx-auto px-6 py-24 text-center" data-testid="checkout-result">
      <div className={`w-16 h-16 rounded-full border border-white/10 flex items-center justify-center mx-auto ${copy.color}`}>
        <Icon size={30} />
      </div>
      <h1 className="font-display text-4xl md:text-5xl tracking-tight mt-6">
        {lang === "it" ? copy.title_it : copy.title_en}
      </h1>
      <p className="text-zinc-400 mt-3 max-w-md mx-auto">
        {lang === "it" ? copy.body_it : copy.body_en}
      </p>
      <div className="mt-8 inline-flex flex-col gap-1 border border-white/10 rounded-xl px-6 py-4">
        <span className="label-eyebrow">Riferimento</span>
        <span className="font-mono text-white text-lg" data-testid="result-order-ref">{orderId}</span>
      </div>
      {!isFinal && (
        <p className="text-xs font-mono text-zinc-600 mt-6">
          {lang === "it" ? "Aggiornamento automatico ogni 5 secondi…" : "Auto-refreshing every 5 seconds…"}
        </p>
      )}
      <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
        <Link to="/" className="pill-btn bg-white text-black hover:bg-zinc-200">
          {lang === "it" ? "Torna alla home" : "Back to home"}
        </Link>
        <Link to="/support" className="pill-btn border border-white/20 text-white hover:bg-white/5">
          {lang === "it" ? "Assistenza" : "Support"}
        </Link>
      </div>
    </div>
  );
}

export function CheckoutCancelled() {
  const { orderId } = useParams();
  const { lang } = useLang();
  return (
    <div className="max-w-[720px] mx-auto px-6 py-24 text-center" data-testid="checkout-cancelled">
      <div className="w-16 h-16 rounded-full border border-white/10 flex items-center justify-center mx-auto text-zinc-400">
        <XCircle size={30} />
      </div>
      <h1 className="font-display text-4xl md:text-5xl tracking-tight mt-6">
        {lang === "it" ? "Pagamento annullato" : "Payment cancelled"}
      </h1>
      <p className="text-zinc-400 mt-3 max-w-md mx-auto">
        {lang === "it"
          ? "Hai annullato il pagamento. Nessun addebito è stato effettuato. Puoi riprovare quando vuoi."
          : "You cancelled the payment. Nothing was charged. You can try again anytime."}
      </p>
      {orderId && (
        <div className="mt-8 inline-flex flex-col gap-1 border border-white/10 rounded-xl px-6 py-4">
          <span className="label-eyebrow">Riferimento</span>
          <span className="font-mono text-white text-lg">{orderId}</span>
        </div>
      )}
      <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
        <Link to="/catalog" className="pill-btn bg-white text-black hover:bg-zinc-200">
          {lang === "it" ? "Torna al catalogo" : "Back to catalog"}
        </Link>
        <Link to="/checkout" className="pill-btn border border-white/20 text-white hover:bg-white/5">
          {lang === "it" ? "Riprova checkout" : "Retry checkout"}
        </Link>
      </div>
    </div>
  );
}
