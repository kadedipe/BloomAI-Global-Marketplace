from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from . import hardening
from .database import get_db
from .models import FulfillmentStatus, OrderStatus, RefundStatus, Role, User
from .security import current_user


DELIVERY_METHOD_LABELS = {
    "local_delivery": "Local delivery",
    "vendor_delivery": "Vendor delivery",
    "pickup": "Customer pickup",
    "independent_courier": "Independent courier",
}


class FulfillmentUpdate(hardening.FulfillmentUpdate):
    delivery_method: str | None = Field(default=None, max_length=40)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _manual_method(value: str | None) -> str | None:
    cleaned = _clean(value)
    if cleaned is None:
        return None
    normalized = cleaned.lower().replace("-", "_").replace(" ", "_")
    if normalized not in DELIVERY_METHOD_LABELS:
        supported = ", ".join(DELIVERY_METHOD_LABELS)
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported no-tracking delivery method. Choose one of: {supported}",
        )
    return normalized


async def hardened_fulfillment(
    order_id: int,
    payload: FulfillmentUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fulfill paid orders with either tracked shipping or a legitimate no-tracking method."""
    order = await hardening.locked_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    product = await hardening.locked_product(db, order.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if user.role not in {Role.vendor, Role.admin} or (
        user.role == Role.vendor and product.vendor_id != user.id
    ):
        raise HTTPException(status_code=403, detail="Vendor access required")
    if order.status != OrderStatus.paid:
        raise HTTPException(status_code=409, detail="Only paid orders can be fulfilled")
    if order.refund_status in {RefundStatus.processing, RefundStatus.refunded}:
        raise HTTPException(status_code=409, detail="Refunded orders cannot be fulfilled")
    if payload.status == FulfillmentStatus.cancelled:
        raise HTTPException(
            status_code=409,
            detail="Paid orders use the refund workflow rather than fulfillment cancellation",
        )

    carrier = _clean(payload.carrier)
    tracking_number = _clean(payload.tracking_number)
    delivery_method = _manual_method(payload.delivery_method)

    if payload.status == FulfillmentStatus.shipped:
        tracked = carrier is not None and tracking_number is not None
        partial_tracking = (carrier is None) != (tracking_number is None)
        if partial_tracking:
            raise HTTPException(
                status_code=422,
                detail="Tracked shipping requires both carrier and tracking number",
            )
        if tracked and delivery_method:
            raise HTTPException(
                status_code=422,
                detail="Choose either tracked shipping or a no-tracking delivery method, not both",
            )
        if not tracked and not delivery_method:
            raise HTTPException(
                status_code=422,
                detail="Choose tracked shipping or a no-tracking delivery method",
            )

    allowed = {
        FulfillmentStatus.unfulfilled: {
            FulfillmentStatus.processing,
            FulfillmentStatus.shipped,
        },
        FulfillmentStatus.processing: {FulfillmentStatus.shipped},
        FulfillmentStatus.shipped: {FulfillmentStatus.delivered},
        FulfillmentStatus.delivered: set(),
        FulfillmentStatus.cancelled: set(),
    }
    if (
        payload.status != order.fulfillment_status
        and payload.status not in allowed[order.fulfillment_status]
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot move fulfillment from {order.fulfillment_status.value} "
                f"to {payload.status.value}"
            ),
        )

    order.fulfillment_status = payload.status
    now = datetime.now(timezone.utc)
    if payload.status == FulfillmentStatus.shipped:
        order.shipped_at = now
        if delivery_method:
            order.carrier = DELIVERY_METHOD_LABELS[delivery_method]
            order.tracking_number = None
            order.tracking_provider_id = None
            order.tracking_status = "manual"
            order.tracking_updated_at = now
        else:
            order.carrier = carrier
            order.tracking_number = tracking_number
            registration = await hardening.register_tracking(
                tracking_number=order.tracking_number,
                order_id=order.id,
                carrier=order.carrier,
            )
            if registration:
                order.tracking_provider_id = str(registration.get("id") or "") or None
                order.tracking_status = str(
                    registration.get("tag")
                    or registration.get("status")
                    or "registered"
                )
            else:
                order.tracking_status = (
                    "manual"
                    if not hardening.settings.aftership_enabled
                    else "registration_failed"
                )
            order.tracking_updated_at = now
    elif payload.status == FulfillmentStatus.delivered:
        order.delivered_at = now
        order.tracking_status = "Delivered"
        order.tracking_updated_at = now

    await hardening.create_notification(
        db,
        user_id=order.buyer_id,
        type=f"order.{payload.status.value}",
        title=f"Order {payload.status.value}",
        message=f"Order #{order.id} for {product.name} is now {payload.status.value}.",
        link="/#orders",
    )
    await db.commit()
    return {
        "id": order.id,
        "status": order.status.value,
        "fulfillment_status": order.fulfillment_status.value,
        "carrier": order.carrier,
        "tracking_number": order.tracking_number,
        "tracking_status": order.tracking_status,
        "tracking_provider_id": order.tracking_provider_id,
        "delivery_method": delivery_method,
        "shipped_at": order.shipped_at,
        "delivered_at": order.delivered_at,
    }
