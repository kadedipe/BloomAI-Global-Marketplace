import csv
import io
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .admin import require_admin
from .database import get_db
from .models import Order, OrderStatus, Product, Role, User
from .segmentation import ParticipantProfile

router = APIRouter(prefix="/api/v1/admin/executive", tags=["admin-executive"])


def month_key(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m")


def pct(numerator: float, denominator: float) -> float:
    return round((numerator / denominator) * 100, 2) if denominator else 0.0


def pdf_bytes(lines: list[str]) -> bytes:
    safe = []
    for line in lines:
        value = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        safe.append(value[:110])
    stream = ["BT", "/F1 11 Tf", "50 790 Td"]
    for index, line in enumerate(safe):
        if index:
            stream.append("0 -16 Td")
        stream.append(f"({line}) Tj")
    stream.append("ET")
    body = "\n".join(stream).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(body) + body + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    result = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(result))
        result.extend(f"{index} 0 obj\n".encode())
        result.extend(obj)
        result.extend(b"\nendobj\n")
    xref = len(result)
    result.extend(f"xref\n0 {len(objects)+1}\n".encode())
    result.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        result.extend(f"{offset:010d} 00000 n \n".encode())
    result.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(result)


async def dataset(db: AsyncSession):
    users = (await db.execute(select(User))).scalars().all()
    products = (await db.execute(select(Product))).scalars().all()
    orders = (await db.execute(select(Order))).scalars().all()
    profiles = (await db.execute(select(ParticipantProfile))).scalars().all()
    return users, products, orders, {profile.user_id: profile for profile in profiles}


def build_dashboard(users, products, orders, profiles, months: int = 12, inactive_days: int = 90):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=31 * max(1, months - 1))
    paid = [order for order in orders if order.status == OrderStatus.paid]
    customers = [user for user in users if user.role == Role.customer]
    vendors = [user for user in users if user.role == Role.vendor]
    product_by_id = {product.id: product for product in products}

    revenue_by_month = defaultdict(lambda: {"revenue": 0.0, "orders": 0})
    for order in paid:
        stamp = order.paid_at or order.created_at
        if stamp >= start:
            bucket = revenue_by_month[month_key(stamp)]
            bucket["revenue"] += float(order.total)
            bucket["orders"] += 1
    revenue_trends = [
        {"month": key, "revenue": round(value["revenue"], 2), "paid_orders": value["orders"]}
        for key, value in sorted(revenue_by_month.items())
    ]

    acquisition = Counter(month_key(user.created_at) for user in customers if user.created_at >= start)
    customer_orders = Counter(order.buyer_id for order in paid)
    buyers = [customer_id for customer_id, count in customer_orders.items() if count >= 1]
    repeat_buyers = [customer_id for customer_id, count in customer_orders.items() if count >= 2]

    vendor_stats = defaultdict(lambda: {"revenue": 0.0, "orders": 0, "customers": set(), "products": 0})
    customer_spend = defaultdict(float)
    for product in products:
        vendor_stats[product.vendor_id]["products"] += 1
    for order in paid:
        customer_spend[order.buyer_id] += float(order.total)
        product = product_by_id.get(order.product_id)
        if not product:
            continue
        row = vendor_stats[product.vendor_id]
        row["revenue"] += float(order.total)
        row["orders"] += 1
        row["customers"].add(order.buyer_id)
    vendor_ranking = []
    for vendor in vendors:
        row = vendor_stats[vendor.id]
        vendor_ranking.append({
            "vendor_id": vendor.id,
            "vendor_name": vendor.name,
            "organization_name": getattr(profiles.get(vendor.id), "organization_name", None),
            "revenue": round(row["revenue"], 2),
            "paid_orders": row["orders"],
            "unique_customers": len(row["customers"]),
            "products": row["products"],
        })
    vendor_ranking.sort(key=lambda item: (item["revenue"], item["paid_orders"]), reverse=True)

    geography = defaultdict(lambda: {"customers": 0, "vendors": 0, "revenue": 0.0})
    geographic_points = []
    geocoded_count = 0
    for user in customers + vendors:
        profile = profiles.get(user.id)
        country = (getattr(profile, "country", None) or "Unclassified").strip()
        geography[country]["customers" if user.role == Role.customer else "vendors"] += 1
        latitude = getattr(profile, "latitude", None)
        longitude = getattr(profile, "longitude", None)
        if latitude is not None and longitude is not None:
            geocoded_count += 1
            value = (
                customer_spend[user.id]
                if user.role == Role.customer
                else vendor_stats[user.id]["revenue"]
            )
            geographic_points.append(
                {
                    "user_id": user.id,
                    "name": user.name,
                    "role": user.role.value,
                    "organization_name": getattr(profile, "organization_name", None),
                    "category": getattr(getattr(profile, "category", None), "value", "unclassified"),
                    "country": getattr(profile, "country", None),
                    "city": getattr(profile, "city", None),
                    "region": getattr(profile, "region", None),
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "geocoding_source": getattr(profile, "geocoding_source", None),
                    "value": round(value, 2),
                }
            )
    for order in paid:
        profile = profiles.get(order.buyer_id)
        country = (getattr(profile, "country", None) or "Unclassified").strip()
        geography[country]["revenue"] += float(order.total)
    geography_rows = [
        {"country": country, "customers": values["customers"], "vendors": values["vendors"], "revenue": round(values["revenue"], 2)}
        for country, values in geography.items()
    ]
    geography_rows.sort(key=lambda item: (item["revenue"], item["customers"] + item["vendors"]), reverse=True)
    geographic_points.sort(key=lambda item: item["value"], reverse=True)

    current_cutoff = now - timedelta(days=30)
    previous_cutoff = now - timedelta(days=60)
    category_growth = defaultdict(lambda: {"current": 0, "previous": 0})
    for user in customers + vendors:
        profile = profiles.get(user.id)
        category = getattr(getattr(profile, "category", None), "value", "unclassified")
        if user.created_at >= current_cutoff:
            category_growth[category]["current"] += 1
        elif user.created_at >= previous_cutoff:
            category_growth[category]["previous"] += 1
    category_rows = []
    for category, values in category_growth.items():
        previous = values["previous"]
        current = values["current"]
        growth = round(((current - previous) / previous) * 100, 2) if previous else (100.0 if current else 0.0)
        category_rows.append({"category": category, "current_30d": current, "previous_30d": previous, "growth_percent": growth})
    category_rows.sort(key=lambda item: (item["growth_percent"], item["current_30d"]), reverse=True)

    last_activity = {user.id: user.created_at for user in customers + vendors}
    for product in products:
        last_activity[product.vendor_id] = max(last_activity.get(product.vendor_id, product.created_at), product.created_at)
    for order in orders:
        last_activity[order.buyer_id] = max(last_activity.get(order.buyer_id, order.created_at), order.paid_at or order.created_at)
        product = product_by_id.get(order.product_id)
        if product:
            last_activity[product.vendor_id] = max(last_activity.get(product.vendor_id, order.created_at), order.paid_at or order.created_at)
    inactive_cutoff = now - timedelta(days=inactive_days)
    inactive = []
    for user in customers + vendors:
        stamp = last_activity[user.id]
        if stamp < inactive_cutoff:
            inactive.append({
                "user_id": user.id,
                "name": user.name,
                "role": user.role.value,
                "organization_name": getattr(profiles.get(user.id), "organization_name", None),
                "country": getattr(profiles.get(user.id), "country", None),
                "last_activity_at": stamp,
                "inactive_days": (now - stamp).days,
            })
    inactive.sort(key=lambda item: item["inactive_days"], reverse=True)

    gross_revenue = sum(float(order.total) for order in paid)
    total_orders = len(orders)
    paid_orders = len(paid)
    marketplace_participants = len(customers) + len(vendors)
    return {
        "generated_at": now,
        "definitions": {
            "conversion_rate": "Paid orders divided by all initiated orders.",
            "retention_rate": "Customers with 2+ paid purchases divided by customers with at least 1 paid purchase.",
            "inactive_account": f"No recorded marketplace activity for at least {inactive_days} days.",
            "geographic_map": "Map markers use stored participant latitude/longitude. Country aggregates remain available for records without coordinates.",
        },
        "kpis": {
            "gross_revenue": round(gross_revenue, 2),
            "average_order_value": round(gross_revenue / paid_orders, 2) if paid_orders else 0.0,
            "checkout_conversion_rate": pct(paid_orders, total_orders),
            "repeat_purchase_rate": pct(len(repeat_buyers), len(buyers)),
            "active_buyers": len(buyers),
            "repeat_buyers": len(repeat_buyers),
            "inactive_accounts": len(inactive),
            "geocoded_participants": geocoded_count,
            "geocoding_coverage_rate": pct(geocoded_count, marketplace_participants),
        },
        "revenue_trends": revenue_trends,
        "customer_acquisition": [{"month": key, "new_customers": acquisition[key]} for key in sorted(acquisition)],
        "retention": {"buyers": len(buyers), "repeat_buyers": len(repeat_buyers), "rate": pct(len(repeat_buyers), len(buyers))},
        "vendor_ranking": vendor_ranking[:25],
        "geography": geography_rows,
        "geographic_points": geographic_points[:500],
        "geographic_coverage": {
            "geocoded": geocoded_count,
            "total_participants": marketplace_participants,
            "coverage_rate": pct(geocoded_count, marketplace_participants),
            "ungeocoded": max(0, marketplace_participants - geocoded_count),
        },
        "category_growth": category_rows,
        "inactive_accounts": inactive[:200],
    }


@router.get("/dashboard")
async def executive_dashboard(
    months: int = Query(default=12, ge=3, le=36),
    inactive_days: int = Query(default=90, ge=30, le=730),
    _=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    users, products, orders, profiles = await dataset(db)
    return build_dashboard(users, products, orders, profiles, months, inactive_days)


@router.get("/export.csv")
async def export_csv(_=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    users, products, orders, profiles = await dataset(db)
    report = build_dashboard(users, products, orders, profiles)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["BloomAI Executive Analytics Report"])
    writer.writerow(["Generated", report["generated_at"].isoformat()])
    writer.writerow([])
    writer.writerow(["KPI", "Value"])
    for key, value in report["kpis"].items():
        writer.writerow([key, value])
    writer.writerow([])
    writer.writerow(["Vendor", "Organization", "Revenue", "Paid Orders", "Unique Customers", "Products"])
    for row in report["vendor_ranking"]:
        writer.writerow([row["vendor_name"], row["organization_name"] or "", row["revenue"], row["paid_orders"], row["unique_customers"], row["products"]])
    writer.writerow([])
    writer.writerow(["Country", "Customers", "Vendors", "Revenue"])
    for row in report["geography"]:
        writer.writerow([row["country"], row["customers"], row["vendors"], row["revenue"]])
    writer.writerow([])
    writer.writerow(["Mapped participant", "Role", "City", "Region", "Country", "Latitude", "Longitude", "Value"])
    for row in report["geographic_points"]:
        writer.writerow([row["name"], row["role"], row["city"] or "", row["region"] or "", row["country"] or "", row["latitude"], row["longitude"], row["value"]])
    payload = output.getvalue().encode("utf-8")
    return StreamingResponse(io.BytesIO(payload), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=bloomai-executive-report.csv"})


@router.get("/export.pdf")
async def export_pdf(_=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    users, products, orders, profiles = await dataset(db)
    report = build_dashboard(users, products, orders, profiles)
    kpi = report["kpis"]
    lines = [
        "BloomAI Executive Analytics Report",
        f"Generated: {report['generated_at'].strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"Gross revenue: {kpi['gross_revenue']:.2f}",
        f"Average order value: {kpi['average_order_value']:.2f}",
        f"Checkout conversion rate: {kpi['checkout_conversion_rate']:.2f}%",
        f"Repeat purchase rate: {kpi['repeat_purchase_rate']:.2f}%",
        f"Active buyers: {kpi['active_buyers']}",
        f"Repeat buyers: {kpi['repeat_buyers']}",
        f"Inactive accounts: {kpi['inactive_accounts']}",
        f"Geocoding coverage: {kpi['geocoding_coverage_rate']:.2f}% ({kpi['geocoded_participants']} participants)",
        "",
        "Top vendors by revenue:",
    ]
    for index, row in enumerate(report["vendor_ranking"][:10], start=1):
        lines.append(f"{index}. {row['vendor_name']} - revenue {row['revenue']:.2f}, {row['paid_orders']} paid orders")
    lines.extend(["", "Top markets by revenue:"])
    for row in report["geography"][:10]:
        lines.append(f"{row['country']} - revenue {row['revenue']:.2f}, customers {row['customers']}, vendors {row['vendors']}")
    return Response(content=pdf_bytes(lines), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=bloomai-executive-report.pdf"})
