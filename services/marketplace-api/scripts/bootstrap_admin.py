from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.admin_bootstrap import bootstrap_admin
from app.database import SessionLocal


REQUIRED_ENV = (
    "BLOOMAI_ADMIN_EMAIL",
    "BLOOMAI_ADMIN_PASSWORD",
    "BLOOMAI_ADMIN_NAME",
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(
        description="Create or rotate credentials for an existing BloomAI administrator."
    )
    value.add_argument(
        "--update-existing",
        action="store_true",
        help="Rotate the password/name only when the configured email already belongs to an admin.",
    )
    return value


def environment() -> dict[str, str]:
    missing = [key for key in REQUIRED_ENV if not os.getenv(key)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
    return {
        "email": os.environ["BLOOMAI_ADMIN_EMAIL"],
        "password": os.environ["BLOOMAI_ADMIN_PASSWORD"],
        "name": os.environ["BLOOMAI_ADMIN_NAME"],
    }


async def run(update_existing: bool) -> int:
    values = environment()
    async with SessionLocal() as db:
        result = await bootstrap_admin(db, update_existing=update_existing, **values)

    if result.created:
        print(f"Created BloomAI administrator: {result.user.email}")
    elif result.credentials_updated:
        print(f"Updated BloomAI administrator credentials: {result.user.email}")
    else:
        print(
            "Administrator already exists; no credentials changed. "
            "Use --update-existing to rotate them."
        )
    return 0


def main() -> int:
    args = parser().parse_args()
    try:
        return asyncio.run(run(args.update_existing))
    except (RuntimeError, ValueError) as error:
        print(f"Admin bootstrap failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
