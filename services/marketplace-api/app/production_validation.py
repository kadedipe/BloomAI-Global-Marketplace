from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .database import get_db
from .models import FulfillmentStatus, Notification, Order, OrderStatus, Product, RefundStatus, Role, User
from .security import current_user

router = APIRouter(prefix="/admin/commerce", tags=["admin-commerce-validation"])
settings = get_settings()


def require_admin(user: User) -> None:
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Administrator access required")


def public_api_base(request: Request) -> str:
    configured = settings.public_api_base_url.strip().rstrip("/")
    if configured:
        return configured
    return str(request.base_url).rstrip("/")


def paystack_mode() -> str:
    key = settings.paystack_secret_key.strip()
    if not key:
        return "unconfigured"
    if key.startswith("sk_test_"):
        return "test"
    if key.startswith("sk_live_"):
        return "live"
    return "configured"


@router.get("/readiness")
async def commerce_readiness(
    request: Request,
    user: User = Depends(current_user),
):
    require_admin(user)
    api_base = public_api_base(request)
    paystack_webhook = f"{api_base}/api/v1/payments/webhook"
    aftership_webhook = f"{api_base}/api/v1/shipping/aftership/webhook"

    checks = {
        "production_environment": settings.environment == "production",
        "postgres_database": settings.database_url.startswith("postgresql+asyncpg://"),
        "public_api_https": api_base.startswith("https://"),
        "web_base_https": settings.web_base_url.startswith("https://"),
        "paystack_configured": settings.paystack_enabled,
        "paystack_callback_https": settings.paystack_callback_url.startswith("https://"),
        "aftership_api_configured": settings.aftership_enabled,
        "aftership_webhook_secret_configured": bool(settings.aftership_webhook_secret),
        "reservation_window_valid": settings.order_reservation_minutes >= 5,
    }
    blockers = [name for name, ok in checks.items() if not ok]
    warnings: list[str] = []
    if settings.shipping_flat_amount == 0:
        warnings.append("SHIPPING_FLAT_AMOUNT is 0; confirm that free shipping is intentional.")
    if settings.sales_tax_percent == 0:
        warnings.append("SALES_TAX_PERCENT is 0; confirm that zero tax is correct for the active jurisdiction.")
    if paystack_mode() == "live":
        warnings.append("Paystack is using a live key. Use a deliberately controlled low-value order for validation.")

    return {
        "ready": not blockers,
        "environment": settings.environment,
        "api_base_url": api_base,
        "web_base_url": settings.web_base_url,
        "provider_state": {
            "paystack": {
                "configured": settings.paystack_enabled,
                "mode": paystack_mode(),
                "callback_url": settings.paystack_callback_url or None,
                "webhook_url": paystack_webhook,
            },
            "aftership": {
                "api_configured": settings.aftership_enabled,
                "webhook_secret_configured": bool(settings.aftership_webhook_secret),
                "webhook_url": aftership_webhook,
                "api_version": settings.aftership_api_version,
            },
        },
        "commerce_policy": {
            "reservation_minutes": settings.order_reservation_minutes,
            "shipping_flat_amount": settings.shipping_flat_amount,
            "shipping_free_threshold": settings.shipping_free_threshold,
            "sales_tax_percent": settings.sales_tax_percent,
        },
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
    }


@router.get("/orders/{order_id}/audit")
async def commerce_order_audit(
    order_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    require_admin(user)
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    product = await db.get(Product, order.product_id)
    if not product:
        raise HTTPException(status_code=409, detail="Order product no longer exists")

    issues: list[str] = []
    subtotal = order.subtotal or (order.unit_price * order.quantity)
    calculated_total = Decimal(subtotal) + Decimal(order.shipping_amount) + Decimal(order.tax_amount)
    if calculated_total != order.total:
        issues.append("Stored total does not equal subtotal + shipping + tax.")
    if order.status == OrderStatus.paid and order.inventory_reserved:
        issues.append("Paid order still has inventory reserved instead of consumed.")
    if order.status == OrderStatus.paid and not order.provider_transaction_id:
        issues.append("Paid order is missing provider_transaction_id.")
    if order.status == OrderStatus.pending and order.inventory_reserved and not order.reservation_expires_at:
        issues.append("Pending inventory reservation has no expiry timestamp.")
    if order.fulfillment_status in {FulfillmentStatus.shipped, FulfillmentStatus.delivered}:
        if not order.carrier or not order.tracking_number:
            issues.append("Shipped/delivered order is missing carrier or tracking number.")
    if order.fulfillment_status == FulfillmentStatus.delivered and not order.delivered_at:
        issues.append("Delivered order is missing delivered_at.")
    if order.refund_status == RefundStatus.refunded and not order.refund_processed_at:
        issues.append("Refunded order is missing refund_processed_at.")

    related_notifications = (
        await db.execute(
            select(func.count(Notification.id)).where(
                Notification.message.contains(f"order #{order.id}")
            )
        )
    ).scalar_one()
    paid_orders = (
        await db.execute(select(func.count(Order.id)).where(Order.status == OrderStatus.paid))
    ).scalar_one()
    gross_revenue = (
        await db.execute(
            select(func.coalesce(func.sum(Order.total), 0)).where(Order.status == OrderStatus.paid)
        )
    ).scalar_one()

    return {
        "consistent": not issues,
        "issues": issues,
        "order": {
            "id": order.id,
            "reference": order.reference,
            "status": order.status.value,
            "fulfillment_status": order.fulfillment_status.value,
            "refund_status": order.refund_status.value,
            "refund_provider_status": order.refund_provider_status,
            "inventory_reserved": order.inventory_reserved,
            "reservation_expires_at": order.reservation_expires_at,
            "subtotal": subtotal,
            "shipping_amount": order.shipping_amount,
            "tax_amount": order.tax_amount,
            "total": order.total,
            "currency": order.currency,
            "provider_transaction_present": bool(order.provider_transaction_id),
            "receipt_available": order.status == OrderStatus.paid and bool(order.paid_at),
            "carrier": order.carrier,
            "tracking_number": order.tracking_number,
            "tracking_status": order.tracking_status,
            "tracking_provider_present": bool(order.tracking_provider_id),
            "shipped_at": order.shipped_at,
            "delivered_at": order.delivered_at,
            "refund_processed_at": order.refund_processed_at,
        },
        "product": {
            "id": product.id,
            "name": product.name,
            "inventory_quantity": product.inventory_quantity,
            "is_active": product.is_active,
        },
        "evidence": {
            "related_notification_count": related_notifications,
            "analytics_paid_order_count": paid_orders,
            "analytics_gross_revenue": gross_revenue,
        },
    }
