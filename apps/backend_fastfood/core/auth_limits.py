"""Database-backed limits shared by every API worker."""
import hashlib
import time
from datetime import datetime, timezone
from fastapi import Depends, Request, HTTPException
from sqlalchemy import text, select
from db.session import get_db
from models.platform_setting import PlatformSetting
from core.exceptions import AuthenticationError

async def security_number(db, key, default, minimum=1, maximum=100):
    value = await db.scalar(select(PlatformSetting.value).where(PlatformSetting.key == key))
    try:
        return max(minimum, min(maximum, int(value)))
    except (TypeError, ValueError):
        return default

async def check_session_age(db, payload):
    hours = await security_number(db, "session_timeout_hours", 12, 1, 168)
    if time.time() - payload.get("iat", 0) > hours * 3600:
        raise AuthenticationError("Session expired. Sign in again.")

async def limit_auth(request: Request, db=Depends(get_db)):
    if request.method != "POST":
        return
    if request.url.path.endswith(("/refresh", "/logout")):
        return
    try:
        data = await request.json()
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    attempts = await security_number(db, "max_login_attempts", 5, 3, 30)
    ip = request.client.host if request.client else "unknown"
    identity = str(data.get("email") or data.get("username") or data.get("user_id") or ip).lower()
    window = int(time.time()) // 900
    # Account limit and a broader per-IP limit apply even if identities vary.
    for key, ceiling in [("account:" + identity, attempts), ("ip:" + ip, max(30, attempts * 6))]:
        digest = hashlib.sha256((request.url.path + ":" + key).encode()).hexdigest()
        count = await db.scalar(text("""
                        INSERT INTO auth_rate_limits (key, "window", attempts) VALUES (:key, :window, 1)
            ON CONFLICT (key) DO UPDATE SET
                            attempts = CASE WHEN auth_rate_limits."window" = EXCLUDED."window"
                THEN auth_rate_limits.attempts + 1 ELSE 1 END,
                            "window" = EXCLUDED."window" RETURNING attempts
        """), {"key": digest, "window": window})
        await db.commit()
        if count > ceiling:
            raise HTTPException(429, "Too many authentication attempts. Try again later.",
                headers={"Retry-After": str(900 - int(time.time()) % 900)})
    await db.execute(text('DELETE FROM auth_rate_limits WHERE "window" < :old'), {"old": window - 4})
    await db.commit()
