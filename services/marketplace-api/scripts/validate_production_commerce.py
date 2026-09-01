from __future__ import annotations

import argparse
import json
import os
import sys

import httpx


def env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def request_json(client: httpx.Client, method: str, path: str, **kwargs):
    response = client.request(method, path, **kwargs)
    if response.status_code >= 400:
        detail = response.text[:500]
        raise SystemExit(f"{method} {path} failed with HTTP {response.status_code}: {detail}")
    return response.json() if response.content else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Safely validate BloomAI production commerce configuration and lifecycle evidence."
    )
    parser.add_argument(
        "--order-id",
        type=int,
        help="Audit an existing controlled validation order. This command never creates or pays an order.",
    )
    parser.add_argument(
        "--output",
        help="Optional path for the JSON validation report. Secrets are never included.",
    )
    args = parser.parse_args()

    api_url = env("BLOOMAI_API_URL").rstrip("/")
    admin_email = env("BLOOMAI_ADMIN_EMAIL")
    admin_password = env("BLOOMAI_ADMIN_PASSWORD")

    report: dict = {"api_url": api_url}
    with httpx.Client(base_url=api_url, timeout=20.0, follow_redirects=True) as client:
        live = request_json(client, "GET", "/health/live")
        ready = request_json(client, "GET", "/health/ready")
        report["health"] = {"live": live, "ready": ready}

        request_json(
            client,
            "POST",
            "/api/v1/auth/login",
            json={"email": admin_email, "password": admin_password},
            headers={"Origin": os.getenv("BLOOMAI_WEB_ORIGIN", api_url)},
        )
        me = request_json(client, "GET", "/api/v1/auth/me")
        if me.get("role") != "admin":
            raise SystemExit("Configured validation account is not an administrator")

        readiness = request_json(client, "GET", "/api/v1/admin/commerce/readiness")
        report["commerce_readiness"] = readiness

        if args.order_id:
            audit = request_json(
                client,
                "GET",
                f"/api/v1/admin/commerce/orders/{args.order_id}/audit",
            )
            report["order_audit"] = audit
            if audit["order"]["receipt_available"]:
                receipt = request_json(
                    client,
                    "GET",
                    f"/api/v1/orders/{args.order_id}/receipt",
                )
                report["receipt"] = receipt
            report["executive_analytics"] = request_json(
                client,
                "GET",
                "/api/v1/admin/executive/dashboard",
            ).get("kpis", {})

    payload = json.dumps(report, indent=2, default=str)
    print(payload)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")

    readiness_ok = report["commerce_readiness"]["ready"]
    audit_ok = report.get("order_audit", {}).get("consistent", True)
    return 0 if readiness_ok and audit_ok else 2


if __name__ == "__main__":
    sys.exit(main())
