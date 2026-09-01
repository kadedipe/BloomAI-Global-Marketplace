from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import FulfillmentStatus, Order, OrderStatus, Product, RefundStatus, Role, User
from .notifications import OrderSummaryResponse, create_notification, notify_role, order_summary
from .payments import request as paystack_request
from .security import current_user

router = APIRouter(prefix="/api/v1/orders", tags=["commerce"])


class FulfillmentUpdate(BaseModel):
    status: FulfillmentStatus
    carrier: str | None = Field(default=None, max_length=120)
    tracking_number: str | None = Field(default=None, max_length=160)


class RefundRequest(BaseModel):
    reason: str = Field(min_length=5, max_length=2000)


class RefundReview(BaseModel):
    decision: RefundStatus


class ReceiptResponse(BaseModel):
    receipt_number: str
    order_id: int
    reference: str
    paid_at: datetime
    buyer_name: str
    vendor_name: str
    product_name: str
    quantity: int
    unit_price: Decimal
    total: Decimal
    currency: str
    recipient_name: str | None
    delivery_address: str


async def authorized_order(
    order_id: int,
    user: User,
    db: AsyncSession,
    *,
    vendor_access: bool = True,
) -> tuple[Order, Product]:
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    product = await db.get(Product, order.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    allowed = user.role == Role.admin or order.buyer_id == user.id
    if vendor_access:
        allowed = allowed or (user.role == Role.vendor and product.vendor_id == user.id)
    if not allowed:
        raise HTTPException(status_code=404, detail="Order not found")
    return order, product


@router.get("/{order_id}", response_model=OrderSummaryResponse)
async def order_detail(
    order_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    order, _ = await authorized_order(order_id, user, db)
    return await order_summary(db, order)


@router.patch("/{order_id}/fulfillment", response_model=OrderSummaryResponse)
async def update_fulfillment(
    order_id: int,
    payload: FulfillmentUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    order, product = await authorized_order(order_id, user, db)
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
    if payload.status == FulfillmentStatus.shipped and (
        not payload.carrier or not payload.tracking_number
    ):
        raise HTTPException(
            status_code=422,
            detail="Carrier and tracking number are required when marking an order shipped",
        )
    current = order.fulfillment_status
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
    if payload.status != current and payload.status not in allowed[current]:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot move fulfillment from {current.value} to {payload.status.value}",
        )

    order.fulfillment_status = payload.status
    if payload.carrier:
        order.carrier = payload.carrier.strip()
    if payload.tracking_number:
        order.tracking_number = payload.tracking_number.strip()
    now = datetime.now(timezone.utc)
    if payload.status == FulfillmentStatus.shipped:
        order.shipped_at = now
    elif payload.status == FulfillmentStatus.delivered:
        order.delivered_at = now

    label = payload.status.value.replace("_", " ")
    await create_notification(
        db,
        user_id=order.buyer_id,
        type=f"order.{payload.status.value}",
        title=f"Order {label}",
        message=f"Order #{order.id} for {product.name} is now {label}.",
        link="/#orders",
    )
    await db.commit()
    await db.refresh(order)
    return await order_summary(db, order)


@router.post("/{order_id}/refund-request", response_model=OrderSummaryResponse)
async def request_refund(
    order_id: int,
    payload: RefundRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    order, product = await authorized_order(order_id, user, db, vendor_access=False)
    if order.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Only the buyer can request a refund")
    if order.status != OrderStatus.paid:
        raise HTTPException(status_code=409, detail="Only paid orders can be refunded")
    if order.refund_status not in {RefundStatus.none, RefundStatus.rejected}:
        raise HTTPException(status_code=409, detail="A refund workflow already exists for this order")
    order.refund_status = RefundStatus.requested
    order.refund_reason = payload.reason.strip()
    order.refund_requested_at = datetime.now(timezone.utc)
    await create_notification(
        db,
        user_id=product.vendor_id,
        type="order.refund_requested",
        title="Refund requested",
        message=f"A refund was requested for order #{order.id} for {product.name}.",
        link="/#orders",
    )
    await notify_role(
        db,
        Role.admin,
        type="order.refund_requested",
        title=f"Refund requested for order #{order.id}",
        message=f"Buyer requested a refund for {product.name}.",
        link="/admin.html#activity",
        exclude_user_ids={order.buyer_id, product.vendor_id},
    )
    await db.commit()
    await db.refresh(order)
    return await order_summary(db, order)


@router.patch("/{order_id}/refund-review", response_model=OrderSummaryResponse)
async def review_refund(
    order_id: int,
    payload: RefundReview,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    order, product = await authorized_order(order_id, user, db)
    if user.role not in {Role.vendor, Role.admin} or (
        user.role == Role.vendor and product.vendor_id != user.id
    ):
        raise HTTPException(status_code=403, detail="Vendor access required")
    if order.refund_status != RefundStatus.requested:
        raise HTTPException(status_code=409, detail="No pending refund request exists")
    if payload.decision not in {RefundStatus.approved, RefundStatus.rejected}:
        raise HTTPException(status_code=422, detail="Decision must be approved or rejected")
    order.refund_status = payload.decision
    title = "Refund approved" if payload.decision == RefundStatus.approved else "Refund declined"
    message = (
        f"The refund request for order #{order.id} was approved and awaits payment processing."
        if payload.decision == RefundStatus.approved
        else f"The refund request for order #{order.id} was declined by the seller."
    )
    await create_notification(
        db,
        user_id=order.buyer_id,
        type=f"order.refund_{payload.decision.value}",
        title=title,
        message=message,
        link="/#orders",
    )
    await db.commit()
    await db.refresh(order)
    return await order_summary(db, order)


@router.post("/{order_id}/refund-execute", response_model=OrderSummaryResponse)
async def execute_refund(
    order_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Administrator access required")
    order, product = await authorized_order(order_id, user, db)
    if order.refund_status != RefundStatus.approved:
        raise HTTPException(status_code=409, detail="Refund must be approved before processing")
    if not order.provider_transaction_id:
        raise HTTPException(status_code=409, detail="Payment provider transaction is unavailable")

    data = await paystack_request(
        "POST",
        "/refund",
        json={
            "transaction": order.provider_transaction_id,
            "amount": int(order.total * Decimal("100")),
            "currency": order.currency,
            "customer_note": order.refund_reason or "BloomAI marketplace refund",
            "merchant_note": f"BloomAI order #{order.id}",
        },
    )
    provider_status = str(data.get("status", "")).lower()
    order.refund_status = (
        RefundStatus.refunded
        if provider_status in {"processed", "refunded", "success"}
        else RefundStatus.processing
    )
    if order.refund_status == RefundStatus.refunded:
        order.refund_processed_at = datetime.now(timezone.utc)
    await create_notification(
        db,
        user_id=order.buyer_id,
        type=f"payment.refund_{order.refund_status.value}",
        title="Refund update",
        message=f"Refund for order #{order.id} is {order.refund_status.value}.",
        link="/#orders",
    )
    await create_notification(
        db,
        user_id=product.vendor_id,
        type=f"order.refund_{order.refund_status.value}",
        title="Refund update",
        message=f"Refund for order #{order.id} is {order.refund_status.value}.",
        link="/#orders",
    )
    await db.commit()
    await db.refresh(order)
    return await order_summary(db, order)


@router.get("/{order_id}/receipt", response_model=ReceiptResponse)
async def order_receipt(
    order_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    order, product = await authorized_order(order_id, user, db)
    if order.status != OrderStatus.paid or not order.paid_at:
        raise HTTPException(status_code=409, detail="Receipt is available after payment confirmation")
    buyer = await db.get(User, order.buyer_id)
    vendor = await db.get(User, product.vendor_id)
    address = ", ".join(
        part
        for part in [order.address_line1, order.city, order.region, order.postal_code, order.country]
        if part
    )
    return ReceiptResponse(
        receipt_number=f"BLM-{order.id:08d}",
        order_id=order.id,
        reference=order.reference,
        paid_at=order.paid_at,
        buyer_name=buyer.name if buyer else "Customer",
        vendor_name=vendor.name if vendor else "Vendor",
        product_name=product.name,
        quantity=order.quantity,
        unit_price=order.unit_price,
        total=order.total,
        currency=order.currency,
        recipient_name=order.recipient_name,
        delivery_address=address,
    )
