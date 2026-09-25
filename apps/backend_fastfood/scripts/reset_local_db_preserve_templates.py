"""Reset only the configured local test DB while preserving Business Templates."""

from __future__ import annotations

import asyncio
import argparse
import json
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKUP_SCHEMA = "local_reset_backup"
COLOR_VARIANT_NAMES = {"color", "colors", "colour", "colours"}

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def reset() -> None:
    sys.path.insert(0, str(PROJECT_ROOT))
    from core.config import settings

    url = make_url(settings.DATABASE_URL)
    if url.host not in {"localhost", "127.0.0.1"} or url.database != "fastfood_test":
        raise RuntimeError(
            f"Refusing reset: expected localhost/fastfood_test, got {url.host}/{url.database}."
        )

    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as connection:
        backup_exists = await connection.scalar(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = :name)"
        ), {"name": BACKUP_SCHEMA})
        if backup_exists:
            raise RuntimeError(f"Recovery schema {BACKUP_SCHEMA!r} already exists; reset aborted.")
        template_count = await connection.scalar(text("SELECT count(*) FROM public.business_templates"))
        print(f"Target: {url.host}/{url.database}; preserving {template_count} Business Templates.")
        await connection.execute(text(f'CREATE SCHEMA "{BACKUP_SCHEMA}"'))
        await connection.execute(text(
            f'CREATE TABLE "{BACKUP_SCHEMA}".business_templates AS TABLE public.business_templates'
        ))
        await connection.execute(text("DROP SCHEMA public CASCADE"))
        await connection.execute(text("CREATE SCHEMA public"))
    await engine.dispose()

    migration = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=PROJECT_ROOT,
        check=False,
    )
    if migration.returncode != 0:
        raise RuntimeError(
            f"Alembic failed; preserved templates remain in {BACKUP_SCHEMA}.business_templates."
        )

    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as connection:
        expected = await connection.scalar(text(
            f'SELECT count(*) FROM "{BACKUP_SCHEMA}".business_templates'
        ))
        await connection.execute(text("DELETE FROM public.business_templates"))
        await connection.execute(text(
            f'INSERT INTO public.business_templates SELECT * FROM "{BACKUP_SCHEMA}".business_templates'
        ))
        restored = (await connection.execute(text(
            "SELECT id, config FROM public.business_templates"
        ))).all()
        for template_id, config in restored:
            config = dict(config or {})
            variants = dict(config.get("variants") or {})
            groups = list(variants.get("seed_groups") or [])
            variants["seed_groups"] = [
                group for group in groups
                if " ".join(str(group.get("name", "")).split()).casefold()
                not in COLOR_VARIANT_NAMES
            ]
            config["variants"] = variants
            await connection.execute(text(
                "UPDATE public.business_templates "
                "SET config = CAST(:config AS jsonb) WHERE id = :id"
            ), {"id": template_id, "config": json.dumps(config)})
        actual = await connection.scalar(text("SELECT count(*) FROM public.business_templates"))
        if actual != expected:
            raise RuntimeError(f"Template restore mismatch: expected {expected}, restored {actual}.")
        await connection.execute(text(f'DROP SCHEMA "{BACKUP_SCHEMA}" CASCADE'))
    await engine.dispose()
    print(f"Reset complete; restored {actual} Business Templates.")


async def verify() -> None:
    sys.path.insert(0, str(PROJECT_ROOT))
    from core.config import settings

    url = make_url(settings.DATABASE_URL)
    if url.host not in {"localhost", "127.0.0.1"} or url.database != "fastfood_test":
        raise RuntimeError(
            f"Refusing verification: expected localhost/fastfood_test, got {url.host}/{url.database}."
        )
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as connection:
        tables = (await connection.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        ))).scalars().all()
        nonempty = {}
        for table in tables:
            count = await connection.scalar(text(f'SELECT count(*) FROM public."{table}"'))
            if count:
                nonempty[table] = count
        templates = (await connection.execute(text(
            "SELECT name, config FROM public.business_templates ORDER BY name"
        ))).all()
    await engine.dispose()
    print(
        f"Verified {url.host}/{url.database}; non-empty tables: {nonempty}; "
        f"template variant seeds: "
        f"{[(name, [g.get('name') for g in config.get('variants', {}).get('seed_groups', [])]) for name, config in templates]}"
    )


def parse_args():
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--reset", action="store_true")
    action.add_argument("--verify", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(reset() if args.reset else verify())
