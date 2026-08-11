"""Centralised environment-driven configuration for LicenzPøl.

Rules enforced here:
  * APP_ENV must be one of {development, staging, production}.
  * COMMERCE_ENABLED flips real checkout on/off.
  * In production we fail-closed on missing critical secrets.
"""

import os
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


APP_ENV = (os.environ.get("APP_ENV") or "development").lower().strip()
if APP_ENV not in {"development", "staging", "production"}:
    APP_ENV = "development"

COMMERCE_ENABLED = (os.environ.get("COMMERCE_ENABLED", "false").lower() == "true")
SEARCH_INDEXING_ENABLED = (os.environ.get("SEARCH_INDEXING_ENABLED", "false").lower() == "true")

PUBLIC_SITE_URL = (os.environ.get("PUBLIC_SITE_URL") or "").rstrip("/") or None

CATALOG_PREVIEW_SCOPE = (os.environ.get("CATALOG_PREVIEW_SCOPE") or "all").lower().strip()
if CATALOG_PREVIEW_SCOPE not in {"all", "market"}:
    CATALOG_PREVIEW_SCOPE = "all"

JWT_SECRET = os.environ.get("JWT_SECRET", "")
LICENSE_KEY_ENCRYPTION_KEY = os.environ.get("LICENSE_KEY_ENCRYPTION_KEY", "")
BACKUP_ENCRYPTION_KEY = os.environ.get("BACKUP_ENCRYPTION_KEY", "")

# Brevo
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "supporto@licenzpol.it")
BREVO_SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "LicenzPol")
BREVO_WEBHOOK_SECRET = os.environ.get("BREVO_WEBHOOK_SECRET", "")
EMAIL_DELIVERY_MODE = (os.environ.get("EMAIL_DELIVERY_MODE") or "dry-run").lower().strip()
if EMAIL_DELIVERY_MODE not in {"dry-run", "live"}:
    EMAIL_DELIVERY_MODE = "dry-run"

# Nexi XPay REST API (Hosted Payment Page)
NEXI_ENV = os.environ.get("NEXI_ENV", "sandbox").lower()  # sandbox | production
NEXI_API_KEY = os.environ.get("NEXI_API_KEY", "")
NEXI_TENANT_ID = os.environ.get("NEXI_TENANT_ID", "")
NEXI_MERCHANT_ID = os.environ.get("NEXI_MERCHANT_ID", "")
NEXI_TERMINAL_ID = os.environ.get("NEXI_TERMINAL_ID", "")
NEXI_PUBLIC_API_URL = (os.environ.get("NEXI_PUBLIC_API_URL") or PUBLIC_SITE_URL or "").rstrip("/")

CORS_ORIGINS_RAW = os.environ.get("CORS_ORIGINS", "*")
ALLOWED_HOSTS_RAW = os.environ.get("ALLOWED_HOSTS", "")


def allowed_hosts() -> List[str]:
    hosts = [host.strip() for host in ALLOWED_HOSTS_RAW.split(",") if host.strip()]
    if PUBLIC_SITE_URL:
        public_host = urlparse(PUBLIC_SITE_URL).hostname
        if public_host and public_host not in hosts:
            hosts.append(public_host)
    for local in ("127.0.0.1", "localhost", "testserver"):
        if local not in hosts:
            hosts.append(local)
    return hosts


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
    if not BACKUP_ENCRYPTION_KEY:
        missing.append("BACKUP_ENCRYPTION_KEY")
    if COMMERCE_ENABLED and not NEXI_API_KEY:
        missing.append("NEXI_API_KEY")
    if COMMERCE_ENABLED and not LICENSE_KEY_ENCRYPTION_KEY:
        missing.append("LICENSE_KEY_ENCRYPTION_KEY")
    if COMMERCE_ENABLED and not BREVO_API_KEY:
        missing.append("BREVO_API_KEY")
    if cors_origins() == []:
        missing.append("CORS_ORIGINS (specific hosts)")
    if not allowed_hosts() or "*" in allowed_hosts():
        missing.append("ALLOWED_HOSTS (specific hosts)")
    return missing


def is_staging_or_dev() -> bool:
    return APP_ENV in {"staging", "development"}


def is_production() -> bool:
    return APP_ENV == "production"
