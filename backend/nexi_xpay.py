"""Nexi XPay integration scaffold.

Status: PLACEHOLDER — requires real NEXI_XPAY_ALIAS and NEXI_XPAY_MAC_KEY.

API reference (Nexi XPay Build):
  - Sandbox: https://int-ecommerce.nexi.it/ecomm/ecomm/DispatcherServlet
  - Production: https://ecommerce.nexi.it/ecomm/ecomm/DispatcherServlet

Flow:
  1) `create_payment_request()` returns a signed redirect URL for XPay.
  2) User is redirected there for card entry.
  3) Nexi calls our webhook `/api/payments/nexi/webhook` with the outcome.
  4) We verify the MAC signature, then finalize the order.

Until real credentials are provided the module returns HTTP 503 to keep the
flow honest and prevent silent "fake success" states in production.
"""

import hashlib
import logging
from decimal import Decimal
from typing import Dict, Optional

from config import NEXI_XPAY_ALIAS, NEXI_XPAY_MAC_KEY, NEXI_XPAY_ENV, COMMERCE_ENABLED, is_production

log = logging.getLogger("licenzpol.nexi")

ENDPOINTS = {
    "test": "https://int-ecommerce.nexi.it/ecomm/ecomm/DispatcherServlet",
    "prod": "https://ecommerce.nexi.it/ecomm/ecomm/DispatcherServlet",
}


def is_configured() -> bool:
    return bool(NEXI_XPAY_ALIAS and NEXI_XPAY_MAC_KEY)


def endpoint_url() -> str:
    return ENDPOINTS["prod" if NEXI_XPAY_ENV == "prod" else "test"]


def _mac(params: Dict[str, str]) -> str:
    """Compute Nexi MAC signature for the given request params.

    XPay Build MAC = SHA1(codTrans=...&divisa=...&importo=...<MAC_KEY>).
    """
    raw = f"codTrans={params['codTrans']}&divisa={params['divisa']}&importo={params['importo']}{NEXI_XPAY_MAC_KEY}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def create_payment_request(
    *,
    order_reference: str,
    total_eur: Decimal,
    return_url: str,
    cancel_url: str,
    email: Optional[str] = None,
) -> Dict[str, str]:
    """Return the params + endpoint the frontend can POST to.

    Amount is in cents (Nexi expects integer, no decimals).
    """
    if not COMMERCE_ENABLED:
        raise RuntimeError("Commerce is disabled (COMMERCE_ENABLED=false)")
    if not is_configured():
        raise RuntimeError("Nexi XPay is not configured — set NEXI_XPAY_ALIAS and NEXI_XPAY_MAC_KEY")

    cents = int(Decimal(total_eur).quantize(Decimal("0.01")) * 100)
    params = {
        "alias": NEXI_XPAY_ALIAS,
        "importo": str(cents),
        "divisa": "EUR",
        "codTrans": order_reference[:30],
        "url": return_url,
        "url_back": cancel_url,
    }
    if email:
        params["mail"] = email
    params["mac"] = _mac(params)
    return {"endpoint": endpoint_url(), **params}


def verify_webhook(params: Dict[str, str]) -> bool:
    """Verify the MAC returned in the Nexi webhook."""
    if not is_configured():
        return False
    received = params.get("mac", "")
    raw = (
        f"codTrans={params.get('codTrans','')}"
        f"&esito={params.get('esito','')}"
        f"&importo={params.get('importo','')}"
        f"&divisa={params.get('divisa','')}"
        f"&data={params.get('data','')}"
        f"&orario={params.get('orario','')}"
        f"&codAut={params.get('codAut','')}"
        f"{NEXI_XPAY_MAC_KEY}"
    )
    computed = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    return computed == received
