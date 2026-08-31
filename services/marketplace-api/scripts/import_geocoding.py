#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import csv
import sys
from pathlib import Path

from pydantic import ValidationError

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from app.database import SessionLocal  # noqa: E402
from app.geocoding_import import VerifiedGeocodeRow, import_verified_geocodes  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate or import verified participant coordinates. "
            "This command never geocodes addresses or infers coordinates from country names."
        )
    )
    parser.add_argument("csv_file", type=Path, help="CSV containing verified coordinates")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist valid rows. Without --apply the command is a dry run.",
    )
    return parser.parse_args()


def load_rows(path: Path) -> tuple[list[VerifiedGeocodeRow], list[dict]]:
    rows: list[VerifiedGeocodeRow] = []
    errors: list[dict] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for line_number, raw in enumerate(reader, start=2):
            cleaned = {key: (value.strip() if value is not None else None) for key, value in raw.items()}
            cleaned = {key: (value if value != "" else None) for key, value in cleaned.items()}
            try:
                rows.append(VerifiedGeocodeRow.model_validate(cleaned))
            except ValidationError as error:
                errors.append(
                    {
                        "line": line_number,
                        "identifier": cleaned.get("email") or cleaned.get("user_id"),
                        "error": "; ".join(item["msg"] for item in error.errors()),
                    }
                )
    return rows, errors


async def run() -> int:
    args = parse_args()
    if not args.csv_file.exists():
        print(f"File not found: {args.csv_file}", file=sys.stderr)
        return 2

    rows, validation_errors = load_rows(args.csv_file)
    if validation_errors:
        print("CSV validation errors:")
        for error in validation_errors:
            print(
                f"  line {error['line']} ({error['identifier'] or 'unknown'}): "
                f"{error['error']}"
            )

    async with SessionLocal() as db:
        result = await import_verified_geocodes(db, rows, dry_run=not args.apply)

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"\nVerified geocoding import — {mode}")
    print(f"CSV rows accepted by schema: {len(rows)}")
    print(f"Database-valid participants: {result.valid_rows}")
    print(f"Applied: {result.applied_rows}")
    print(f"Skipped: {result.skipped_rows + len(validation_errors)}")
    for error in result.errors:
        print(f"  row {error['row']} ({error['identifier']}): {error['error']}")

    if validation_errors or result.errors:
        return 1
    if not args.apply:
        print("\nNo database changes were made. Re-run with --apply after reviewing the dry run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
