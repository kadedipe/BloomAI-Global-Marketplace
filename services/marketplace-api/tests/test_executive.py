from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.executive import build_dashboard, pdf_bytes
from app.models import OrderStatus, Role


def user(uid, role, days_ago=0, name=None):
    return SimpleNamespace(
        id=uid,
        role=role,
        name=name or f"User {uid}",
        created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )


def product(pid, vendor_id, days_ago=0):
    return SimpleNamespace(
        id=pid,
        vendor_id=vendor_id,
        created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )


def order(oid, buyer_id, product_id, status, total, days_ago=0):
    stamp = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return SimpleNamespace(
        id=oid,
        buyer_id=buyer_id,
        product_id=product_id,
        status=status,
        total=Decimal(str(total)),
        created_at=stamp,
        paid_at=stamp if status == OrderStatus.paid else None,
    )


def test_executive_kpis_repeat_purchase_and_conversion():
    users = [user(1, Role.customer), user(2, Role.customer), user(10, Role.vendor)]
    products = [product(100, 10)]
    orders = [
        order(1, 1, 100, OrderStatus.paid, 20),
        order(2, 1, 100, OrderStatus.paid, 30),
        order(3, 2, 100, OrderStatus.failed, 40),
    ]
    report = build_dashboard(users, products, orders, {})
    assert report["kpis"]["gross_revenue"] == 50.0
    assert report["kpis"]["average_order_value"] == 25.0
    assert report["kpis"]["checkout_conversion_rate"] == 66.67
    assert report["kpis"]["repeat_purchase_rate"] == 100.0
    assert report["vendor_ranking"][0]["revenue"] == 50.0
    assert report["vendor_ranking"][0]["unique_customers"] == 1


def test_inactive_account_detection_uses_marketplace_activity():
    users = [user(1, Role.customer, 200), user(10, Role.vendor, 200)]
    products = [product(100, 10, 10)]
    report = build_dashboard(users, products, [], {}, inactive_days=90)
    ids = {row["user_id"] for row in report["inactive_accounts"]}
    assert 1 in ids
    assert 10 not in ids


def test_pdf_export_is_valid_pdf_payload():
    payload = pdf_bytes(["BloomAI Executive Analytics Report", "Revenue: 100.00"])
    assert payload.startswith(b"%PDF-1.4")
    assert b"%%EOF" in payload
