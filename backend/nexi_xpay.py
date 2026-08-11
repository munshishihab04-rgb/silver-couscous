"""Nexi XPay REST API integration (Hosted Payment Page).

Documented endpoints:
  Sandbox:    https://xpaysandbox.nexigroup.com/api/phoenix-0.0/psp/api/v1
  Production: https://xpay.nexigroup.com/api/phoenix-0.0/psp/api/v1

Auth: X-Api-Key header. Correlation-Id per request.

Flow:
  1. Client submits an OrderCreate → server persists a pending payment row.
  2. Server POSTs /orders/hpp with amount (cents string), currency, orderId,
     paymentSession { resultUrl, cancelUrl, notificationUrl }.
  3. Nexi returns { hostedPage, securityToken }. Server stores securityToken.
  4. Client is redirected to hostedPage.
  5. Nexi calls our webhook. Verify securityToken (constant-time), then persist.
  6. Never trust the browser redirect — the result page re-queries
     /orders/{orderId} to get the authoritative outcome before fulfilling.
"""

from __future__ import annotations

import hmac
import logging
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional

import httpx

from config import (
    NEXI_ENV, NEXI_API_KEY, NEXI_TENANT_ID, NEXI_MERCHANT_ID,
    NEXI_TERMINAL_ID, NEXI_PUBLIC_API_URL, PUBLIC_SITE_URL,
    COMMERCE_ENABLED,
)

log = logging.getLogger("licenzpol.nexi")

SANDBOX_BASE = "https://xpaysandbox.nexigroup.com/api/phoenix-0.0/psp/api/v1"
PROD_BASE = "https://xpay.nexigroup.com/api/phoenix-0.0/psp/api/v1"


def base_url() -> str:
    return PROD_BASE if NEXI_ENV in {"prod", "production"} else SANDBOX_BASE


def is_configured() -> bool:
    return bool(NEXI_API_KEY)


def _headers() -> Dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Api-Key": NEXI_API_KEY,
        "Correlation-Id": str(uuid.uuid4()),
    }


def _cents(eur: float) -> str:
    """Convert a EUR float to a minor-unit string (Nexi requires cents string)."""
    value = Decimal(str(eur)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return str(int(value * 100))


def _public_site_url() -> str:
    return PUBLIC_SITE_URL or (NEXI_PUBLIC_API_URL or "")


def _api_url() -> str:
    return NEXI_PUBLIC_API_URL or PUBLIC_SITE_URL or ""


async def create_hosted_payment(
    *,
    order_reference: str,
    total_eur: float,
    description: str,
    language: str = "ITA",
) -> Dict[str, Any]:
    """Create a hosted-page payment session on Nexi. Returns
    { orderId, hostedPage, securityToken }.

    Raises NexiError if the API call fails or the response is malformed.
    """
    if not COMMERCE_ENABLED:
        raise NexiError("Commerce is disabled (COMMERCE_ENABLED=false)")
    if not is_configured():
        raise NexiError("Nexi XPay is not configured (missing NEXI_API_KEY)")

    site = _public_site_url()
    api = _api_url()
    if not site or not api:
        raise NexiError("PUBLIC_SITE_URL or NEXI_PUBLIC_API_URL not configured")

    amount = _cents(total_eur)
    order_id = order_reference[:27]  # Nexi limit is ~27 chars for orderId

    payload = {
        "order": {
            "orderId": order_id,
            "amount": amount,
            "currency": "EUR",
            "description": description[:200],
        },
        "paymentSession": {
            "actionType": "PAY",
            "amount": amount,
            "paymentService": "CARDS",
            "captureType": "IMPLICIT",
            "language": language,
            "resultUrl": f"{site}/checkout/result/{order_id}",
            "cancelUrl": f"{site}/checkout/cancelled/{order_id}",
            "notificationUrl": f"{api}/api/payments/nexi/webhook",
        },
    }

    log.info("nexi.create_hpp order=%s amount=%s env=%s", order_id, amount, NEXI_ENV)

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(f"{base_url()}/orders/hpp",
                                     headers=_headers(), json=payload)
    except httpx.HTTPError as e:
        log.error("nexi network error (%s)", type(e).__name__)
        raise NexiError("Nexi network error") from e

    if resp.is_error:
        log.error("nexi hpp request failed with HTTP %s", resp.status_code)
        raise NexiError(f"Nexi HTTP {resp.status_code}")

    data = resp.json()
    hosted_page = data.get("hostedPage")
    security_token = data.get("securityToken")
    if not hosted_page or not security_token:
        log.error("nexi malformed response: keys=%s", list(data.keys()))
        raise NexiError("Nexi response missing hostedPage or securityToken")

    return {
        "orderId": order_id,
        "hostedPage": hosted_page,
        "securityToken": security_token,
    }


async def query_order(order_id: str) -> Dict[str, Any]:
    """Fetch the authoritative status of an order from Nexi."""
    if not is_configured():
        raise NexiError("Nexi not configured")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{base_url()}/orders/{order_id}",
                                    headers=_headers())
    except httpx.HTTPError as e:
        log.warning("nexi query network error (%s)", type(e).__name__)
        raise NexiError("Network error querying Nexi") from e
    if resp.is_error:
        log.warning("nexi query failed with HTTP %s", resp.status_code)
        raise NexiError(f"Nexi HTTP {resp.status_code}")
    return resp.json()


def verify_notification_token(notification_security_token: str,
                              stored_security_token: str) -> bool:
    """Constant-time comparison between the token in the webhook and the token
    saved when the HPP was created for this order."""
    if not notification_security_token or not stored_security_token:
        return False
    return hmac.compare_digest(str(notification_security_token),
                               str(stored_security_token))


# Documented Nexi operationResult values → our internal status map.
NEXI_RESULT_TO_STATUS = {
    "AUTHORIZED": "paid",
    "EXECUTED": "paid",
    "PENDING": "pending_payment",
    "DECLINED": "failed",
    "DENIED_BY_RISK": "failed",
    "THREEDS_FAILED": "failed",
    "CANCELED": "cancelled",
    "CANCELLED": "cancelled",
    "VOIDED": "cancelled",
    "REFUNDED": "refunded",
    "FAILED": "failed",
}


def map_result_to_status(result: Optional[str]) -> str:
    if not result:
        return "pending_payment"
    return NEXI_RESULT_TO_STATUS.get(result.upper(), "pending_payment")


class NexiError(Exception):
    pass
