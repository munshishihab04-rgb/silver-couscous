"""JWT auth for LicenzPol admin panel — bcrypt hashing, Bearer tokens."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Header, HTTPException, Request

JWT_ALG = "HS256"
ACCESS_TTL_HOURS = 24
LOCKOUT_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def _secret() -> str:
    return os.environ["JWT_SECRET"]


def hash_password(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str, email: str, role: str = "admin") -> str:
    payload = {
        "sub": user_id, "email": email, "role": role, "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TTL_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, _secret(), algorithm=JWT_ALG)


def decode_token(token: str) -> dict:
    return jwt.decode(token, _secret(), algorithms=[JWT_ALG])


async def seed_admin(db):
    """Idempotent admin bootstrap from env vars."""
    email = os.environ["ADMIN_EMAIL"].strip().lower()
    pwd = os.environ["ADMIN_PASSWORD"]
    existing = await db.admin_users.find_one({"email": email})
    if existing is None:
        await db.admin_users.insert_one({
            "email": email, "password_hash": hash_password(pwd),
            "name": "Admin", "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    elif not verify_password(pwd, existing.get("password_hash", "")):
        await db.admin_users.update_one(
            {"email": email},
            {"$set": {"password_hash": hash_password(pwd)}},
        )


async def ensure_indexes(db):
    await db.admin_users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")
    await db.login_attempts.create_index("ts")
    await db.analytics_events.create_index([("ts", -1)])
    await db.analytics_events.create_index("event_type")
    await db.analytics_events.create_index("visitor_id")


async def bump_failed(db, identifier: str):
    await db.login_attempts.insert_one({
        "identifier": identifier,
        "ts": datetime.now(timezone.utc).isoformat(),
    })


async def is_locked(db, identifier: str) -> bool:
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
    count = await db.login_attempts.count_documents(
        {"identifier": identifier, "ts": {"$gt": cutoff}}
    )
    return count >= LOCKOUT_ATTEMPTS


async def clear_attempts(db, identifier: str):
    await db.login_attempts.delete_many({"identifier": identifier})


def parse_bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


async def current_admin(request: Request, authorization: Optional[str] = Header(None)):
    """FastAPI dependency: returns the admin doc or raises 401."""
    from bson import ObjectId  # local import to avoid module-load cycle

    token = parse_bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    db = request.app.state.db
    try:
        oid = ObjectId(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid subject")

    user = await db.admin_users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)
    return user
