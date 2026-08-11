"""Brevo (Sendinblue) transactional email service.

Uses async httpx to send transactional emails. Stores messageId on the order
and exposes helpers to send order confirmation + license delivery.

See: https://developers.brevo.com/reference/send-transac-email
"""

import base64
import hashlib
from html import escape
import logging
from typing import Optional, List, Dict, Any

import httpx

from config import BREVO_API_KEY, BREVO_SENDER_EMAIL, BREVO_SENDER_NAME, EMAIL_DELIVERY_MODE

BREVO_URL = "https://api.brevo.com/v3/smtp/email"
log = logging.getLogger("licenzpol.email")


class BrevoError(Exception):
    pass


async def send_email(
    *,
    to_email: str,
    to_name: Optional[str],
    subject: str,
    html: str,
    text: Optional[str] = None,
    tags: Optional[List[str]] = None,
    attachments: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Send a transactional email via Brevo. Returns Brevo messageId.

    attachments: list of {'name': 'file.pdf', 'content': b64_bytes_string}
    """
    if EMAIL_DELIVERY_MODE != "live":
        digest = hashlib.sha256(
            f"{to_email}\n{subject}\n{html}".encode("utf-8")
        ).hexdigest()[:20]
        return f"dry-run:{digest}"
    if not BREVO_API_KEY:
        raise BrevoError("BREVO_API_KEY not configured")

    payload: Dict[str, Any] = {
        "sender": {"email": BREVO_SENDER_EMAIL, "name": BREVO_SENDER_NAME},
        "to": [{"email": to_email, "name": to_name or to_email}],
        "subject": subject,
        "htmlContent": html,
    }
    if text:
        payload["textContent"] = text
    if tags:
        payload["tags"] = tags
    if attachments:
        payload["attachment"] = attachments

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": BREVO_API_KEY,
    }
    timeout = httpx.Timeout(20.0, connect=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(BREVO_URL, headers=headers, json=payload)
    except httpx.HTTPError as e:
        log.error("Brevo network error: %s", e)
        raise BrevoError(f"Network error contacting Brevo: {e}")

    if resp.status_code >= 400:
        # Never log API keys, recipients, payloads or provider response bodies.
        log.error("Brevo API request failed with HTTP %s", resp.status_code)
        raise BrevoError(f"Brevo HTTP {resp.status_code}")
    data = resp.json()
    msg_id = data.get("messageId") or data.get("messageIds", [None])[0]
    if not msg_id:
        raise BrevoError("Brevo response missing messageId")
    return str(msg_id)


def pdf_attachment(name: str, content_bytes: bytes) -> Dict[str, str]:
    return {"name": name, "content": base64.b64encode(content_bytes).decode("ascii")}


# ---------- Templates ------------------------------------------------------

def _base_layout(inner_html: str, footer_note: str = "") -> str:
    return f"""<!doctype html>
<html lang="it"><head><meta charset="utf-8"><title>LicenzPol</title></head>
<body style="margin:0;padding:0;background:#0a0a0c;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;color:#e5e5e7;">
  <div style="max-width:600px;margin:0 auto;padding:32px 24px;">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:24px;">
      <div style="width:32px;height:32px;background:#fff;color:#000;font-weight:700;text-align:center;line-height:32px;border-radius:6px;">LP</div>
      <strong style="font-size:18px;color:#fff;">LicenzPøl</strong>
    </div>
    <div style="background:#0f0f13;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:24px;color:#d4d4d8;line-height:1.55;">
      {inner_html}
    </div>
    <div style="margin-top:24px;font-size:12px;color:#71717a;line-height:1.5;">
      {footer_note}
      <p style="margin:12px 0 0;">DIGITALSOFT DI MUNSHI SHIHAB · Via Aldo Pio Manuzio 24, 40132 Bologna (BO) · P.IVA 04358941203 · REA 588058</p>
      <p style="margin:8px 0 0;">Se hai bisogno di assistenza scrivi a <a href="mailto:supporto@licenzpol.it" style="color:#a78bfa;">supporto@licenzpol.it</a>.</p>
    </div>
  </div>
</body></html>"""


def _safe(value: object) -> str:
    return escape(str(value or ""), quote=True)


def order_confirmation_html(*, customer_name: str, order_ref: str, total_eur: float, items: list, delivery_note: str = "") -> str:
    rows = "".join(
        f'<tr><td style="padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">{_safe(i.get("product_name"))}<br><span style="color:#71717a;font-size:12px;">{_safe(i.get("variant_label"))} × {int(i.get("quantity",1))}</span></td>'
        f'<td style="padding:8px 0;text-align:right;border-bottom:1px solid rgba(255,255,255,0.05);">{(float(i.get("unit_price_eur",0))*int(i.get("quantity",1))):.2f} €</td></tr>'
        for i in items
    )
    inner = f"""
      <h1 style="font-size:22px;color:#fff;margin:0 0 12px;">Ciao {_safe(customer_name)},</h1>
      <p>abbiamo ricevuto il tuo ordine <strong>#{_safe(order_ref)}</strong> e stiamo lavorando alla consegna.</p>
      <table style="width:100%;border-collapse:collapse;margin:16px 0;font-size:14px;">
        {rows}
        <tr><td style="padding:12px 0 0;font-weight:700;color:#fff;">Totale</td>
            <td style="padding:12px 0 0;text-align:right;font-weight:700;color:#fff;">{float(total_eur):.2f} €</td></tr>
      </table>
      <p style="margin:16px 0 0;">{_safe(delivery_note)}</p>
    """
    return _base_layout(inner)


def payment_confirmation_html(*, customer_name: str, order_ref: str, total_eur: float) -> str:
    inner = f"""
      <h1 style="font-size:22px;color:#fff;margin:0 0 12px;">Pagamento confermato</h1>
      <p>Ciao {_safe(customer_name)}, il pagamento di <strong>{float(total_eur):.2f} €</strong> per l'ordine <strong>#{_safe(order_ref)}</strong> è stato ricevuto.</p>
      <p>La consegna digitale verrà elaborata dopo la verifica dell'inventario assegnato all'ordine.</p>
    """
    return _base_layout(inner)


def order_problem_html(*, customer_name: str, order_ref: str, support_code: str) -> str:
    inner = f"""
      <h1 style="font-size:22px;color:#fff;margin:0 0 12px;">Problema con l'ordine</h1>
      <p>Ciao {_safe(customer_name)}, non siamo riusciti a completare automaticamente l'ordine <strong>#{_safe(order_ref)}</strong>.</p>
      <p>Il team di supporto lo verificherà. Codice assistenza: <strong>{_safe(support_code)}</strong>.</p>
    """
    return _base_layout(inner)


def license_delivery_html(*, customer_name: str, order_ref: str, product_name: str, license_key: str, activation_link: Optional[str] = None) -> str:
    activation = f'<p style="margin:12px 0 0;"><a href="{_safe(activation_link)}" style="color:#a78bfa;">Segui la guida di attivazione</a></p>' if activation_link else ""
    inner = f"""
      <h1 style="font-size:22px;color:#fff;margin:0 0 12px;">Ciao {_safe(customer_name)}, la tua licenza è pronta.</h1>
      <p>Ecco la chiave di attivazione per <strong>{_safe(product_name)}</strong> — ordine <strong>#{_safe(order_ref)}</strong>.</p>
      <div style="background:#050508;border:1px dashed rgba(255,255,255,0.15);border-radius:8px;padding:16px;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:16px;color:#fff;letter-spacing:1px;text-align:center;margin:16px 0;">
        {_safe(license_key)}
      </div>
      <p style="font-size:13px;color:#a1a1aa;">Conserva questa email: la chiave viene emessa una sola volta. Se hai perso l'email, contattaci.</p>
      {activation}
    """
    return _base_layout(inner, footer_note="Questa consegna è coperta dai <a href='https://licenzpol.it/legal/terms' style='color:#a78bfa;'>Termini di vendita</a> e dal <a href='https://licenzpol.it/legal/withdrawal' style='color:#a78bfa;'>diritto di recesso digitale</a>.")
