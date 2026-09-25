# services/platform_setting_service.py
#
# CRUD for platform-level key/value settings (platform_settings table).
# Rows are created on first write — an admin never has to pre-seed them.
# Only keys in ALLOWED_KEYS can be written, so the endpoint can't be used to
# stuff arbitrary data into the table.

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.platform_setting import PlatformSetting

# The full set of keys the Platform → Settings page manages. Anything else in a
# PATCH body is ignored.
ALLOWED_KEYS: frozenset[str] = frozenset({
    # Platform
    "platform_name", "default_currency", "default_trial_days", "timezone",
    # Email / SMTP  — override the .env SMTP config for the *platform* recovery mail
    "smtp_host", "smtp_port", "smtp_username", "smtp_password",
    "smtp_from_email", "smtp_from_name",
    # Auth
    "max_login_attempts", "session_timeout_hours",
    # Notifications
    "notifications_enabled",
})


class PlatformSettingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> dict[str, str | None]:
        """Return every setting as a plain {key: value} dict."""
        result = await self.db.execute(select(PlatformSetting).order_by(PlatformSetting.key))
        rows = result.scalars().all()
        return {r.key: r.value for r in rows}

    async def update(self, updates: dict[str, str | None]) -> dict[str, str | None]:
        """
        Update a subset of settings, creating rows that don't exist yet.
        Keys outside ALLOWED_KEYS are silently ignored.
        """
        clean = {k: v for k, v in (updates or {}).items() if k in ALLOWED_KEYS}
        if not clean:
            return await self.get_all()

        from core.exceptions import ValidationError
        for key, bounds in {"max_login_attempts": (3, 30), "session_timeout_hours": (1, 168)}.items():
            if key in clean:
                try:
                    valid = bounds[0] <= int(clean[key]) <= bounds[1]
                except (ValueError, TypeError):
                    valid = False
                if not valid:
                    raise ValidationError(f"{key} must be between {bounds[0]} and {bounds[1]}.")
        existing = {
            row.key: row
            for row in (
                await self.db.execute(
                    select(PlatformSetting).where(PlatformSetting.key.in_(list(clean.keys())))
                )
            ).scalars().all()
        }

        for key, value in clean.items():
            if key in existing:
                existing[key].value = value
            else:
                self.db.add(PlatformSetting(key=key, value=value))

        await self.db.commit()
        return await self.get_all()
