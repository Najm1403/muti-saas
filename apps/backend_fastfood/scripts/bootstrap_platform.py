# scripts/bootstrap_platform.py
#
# Run once after first deployment to create the initial super admin account.
# Safe to run multiple times — skips creation if any platform admin already exists.
#
# Usage:
#   cd backend_fastfood
#   python scripts/bootstrap_platform.py
#
# Credentials are read from environment variables (or .env):
#   PLATFORM_ADMIN_EMAIL     (default: admin@platform.local)
#   PLATFORM_ADMIN_PASSWORD  (required — no default, must be set)
#   PLATFORM_ADMIN_NAME      (default: Super Admin)

from __future__ import annotations

import asyncio
import os
import sys

# Windows requires SelectorEventLoop for psycopg async to work.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Ensure the backend root is on the path so all project imports resolve.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from core.security import hash_password
from db.session import AsyncSessionLocal
from repositories.platform_admin_repository import PlatformAdminRepository


async def bootstrap() -> None:
    email = os.getenv("PLATFORM_ADMIN_EMAIL", "admin@platform.local")
    password = os.getenv("PLATFORM_ADMIN_PASSWORD", "")
    full_name = os.getenv("PLATFORM_ADMIN_NAME", "Super Admin")

    async with AsyncSessionLocal() as db:
        repo = PlatformAdminRepository(db)

        if await repo.exists_any():
            print("Bootstrap skipped — platform admin already exists.")
            print("Use the platform API to manage admins.")
            return

        if not password:
            print("ERROR: PLATFORM_ADMIN_PASSWORD environment variable is not set.")
            print("       Set it in your .env file and try again.")
            sys.exit(1)
        if len(password) < 8:
            print("ERROR: PLATFORM_ADMIN_PASSWORD must be at least 8 characters.")
            sys.exit(1)

        admin = await repo.create(
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            is_super=True,
            role="owner",
        )
        await db.commit()

    print("=" * 55)
    print("  Platform super admin created successfully.")
    print("=" * 55)
    print(f"  Email   : {admin.email}")
    print(f"  Name    : {admin.full_name}")
    print(f"  ID      : {admin.id}")
    print("=" * 55)
    print("  Login at: POST /api/platform/auth/login")
    print("=" * 55)
    print()
    print("  IMPORTANT: Change the password after first login.")
    print()


if __name__ == "__main__":
    asyncio.run(bootstrap())
