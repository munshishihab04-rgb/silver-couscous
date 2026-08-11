"""Render and dispatch non-secret transactional email outbox events."""
from __future__ import annotations

from services import email_brevo, email_outbox


def _subject(value: object) -> str:
    return " ".join(str(value or "").splitlines())[:200]


def render(event: dict) -> tuple[str, str, list[str]]:
    context = event.get("context") or {}
    template = event.get("template")
    reference = context.get("order_reference") or ""
    if template == "order_received":
        return (
            _subject(f"Ordine ricevuto · {reference}"),
            email_brevo.order_confirmation_html(
                customer_name=context.get("customer_name") or event["recipient"],
                order_ref=reference,
                total_eur=float(context.get("total_eur") or 0),
                items=context.get("items") or [],
                delivery_note=context.get("delivery_note") or "",
            ),
            ["order-received"],
        )
    if template == "payment_confirmed":
        return (
            _subject(f"Pagamento confermato · {reference}"),
            email_brevo.payment_confirmation_html(
                customer_name=context.get("customer_name") or event["recipient"],
                order_ref=reference,
                total_eur=float(context.get("total_eur") or 0),
            ),
            ["payment-confirmed"],
        )
    if template == "order_problem":
        return (
            _subject(f"Aggiornamento ordine · {reference}"),
            email_brevo.order_problem_html(
                customer_name=context.get("customer_name") or event["recipient"],
                order_ref=reference,
                support_code=context.get("support_code") or reference,
            ),
            ["order-problem"],
        )
    raise ValueError(f"Unsupported non-secret email template: {template}")


async def dispatch(db, event_key: str) -> dict:
    event = await email_outbox.claim(db, event_key)
    if not event:
        existing = await db.email_outbox.find_one({"event_key": event_key}, {"_id": 0, "status": 1})
        return {"status": "already_processed", "outbox_status": existing.get("status") if existing else None}
    try:
        subject, html, tags = render(event)
        message_id = await email_brevo.send_email(
            to_email=event["recipient"],
            to_name=(event.get("context") or {}).get("customer_name"),
            subject=subject,
            html=html,
            tags=tags,
        )
        dry_run = email_brevo.EMAIL_DELIVERY_MODE != "live"
        await email_outbox.mark_sent(db, event_key, message_id, dry_run=dry_run)
        return {"status": "dry_run" if dry_run else "sent", "message_id": message_id}
    except Exception as exc:
        await email_outbox.mark_failed(db, event_key, type(exc).__name__)
        raise
