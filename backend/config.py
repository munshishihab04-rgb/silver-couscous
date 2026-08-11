"""Centralised environment-driven configuration for LicenzPøl.

Rules enforced here:
  * APP_ENV must be one of {development, staging, production}.
  * COMMERCE_ENABLED flips real checkout on/off.
  * In production we fail-closed on missing critical secrets.
"""

import os
from typing import List


APP_ENV = (os.environ.get("APP_ENV") or "development").lower().strip()
if APP_ENV not in {"development", "staging", "production"}:
    APP_ENV = "development"

COMMERCE_ENABLED = (os.environ.get("COMMERCE_ENABLED", "false").lower() == "true")

PUBLIC_SITE_URL = (os.environ.get("PUBLIC_SITE_URL") or "").rstrip("/") or None

JWT_SECRET = os.environ.get("JWT_SECRET", "")

# Brevo
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "supporto@licenzpol.it")
BREVO_SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "LicenzPol")
BREVO_WEBHOOK_SECRET = os.environ.get("BREVO_WEBHOOK_SECRET", "")

# Nexi XPay (Poste/Nexi Pagamenti)
NEXI_XPAY_ALIAS = os.environ.get("NEXI_XPAY_ALIAS", "")
NEXI_XPAY_MAC_KEY = os.environ.get("NEXI_XPAY_MAC_KEY", "")
NEXI_XPAY_ENV = os.environ.get("NEXI_XPAY_ENV", "test").lower()  # test | prod

CORS_ORIGINS_RAW = os.environ.get("CORS_ORIGINS", "*")


def cors_origins() -> List[str]:
    if APP_ENV == "production":
        # In production we DO NOT allow wildcard.
        origins = [o.strip() for o in CORS_ORIGINS_RAW.split(",") if o.strip() and o.strip() != "*"]
        if not origins and PUBLIC_SITE_URL:
            origins = [PUBLIC_SITE_URL]
        return origins
    return [o.strip() for o in CORS_ORIGINS_RAW.split(",") if o.strip()]


def validate_production_startup() -> List[str]:
    """Return a list of missing critical settings for production. Empty list means OK."""
    if APP_ENV != "production":
        return []
    missing = []
    if not PUBLIC_SITE_URL:
        missing.append("PUBLIC_SITE_URL")
    if not JWT_SECRET or len(JWT_SECRET) < 32:
        missing.append("JWT_SECRET (>=32 chars)")
    if COMMERCE_ENABLED and not (NEXI_XPAY_ALIAS and NEXI_XPAY_MAC_KEY):
        missing.append("NEXI_XPAY_ALIAS/NEXI_XPAY_MAC_KEY")
    if COMMERCE_ENABLED and not BREVO_API_KEY:
        missing.append("BREVO_API_KEY")
    if cors_origins() == []:
        missing.append("CORS_ORIGINS (specific hosts)")
    return missing


def is_staging_or_dev() -> bool:
    return APP_ENV in {"staging", "development"}


def is_production() -> bool:
    return APP_ENV == "production"
