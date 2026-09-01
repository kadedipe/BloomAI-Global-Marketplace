from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .database import get_db
from .models import FulfillmentStatus, Order, OrderStatus, Product, RefundStatus, Role, User
from .notifications import create_notification, notify_role
from .payments import request as paystack_request, valid_webhook_signature
from .security import current_user
from .shipping import register_tracking, valid_aftership_signature

router = APIRouter(prefix="/api/v1", tags=["commerce-hardening"])
settings = get_settings()
CENT = Decimal("0.01")


class QuoteRequest(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=20)
    country: str = Field(default="", max_length=120)


class QuoteResponse(BaseModel):
    product_id: int
    quantity: int
    currency: str
    subtotal: Decimal
    shipping_amount: Decimal
    tax_amount: Decimal
    total: Decimal


class HardenedCheckoutRequest(QuoteRequest):
    recipient_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=5, max_length=40)
    address_line1: str = Field(min_length=4, max_length=240)
    city: str = Field(min_length=2, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=32)
    buyer_note: str | None = Field(default=None, max_length=1000)


class CheckoutResponse(BaseModel):
    order_id: int
    reference: str
    authorization_url: str
    access_code: str
    reservation_expires_at: datetime | None
    subtotal: Decimal
    shipping_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    currency: str


class FulfillmentUpdate(BaseModel):
    status: FulfillmentStatus
    carrier: str | None = Field(default=None, max_length=120)
    tracking_number: str | None = Field(default=None, max_length=160)


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def quote_for(product: Product, quantity: int) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    subtotal = money(product.price * quantity)
    flat_shipping = money(Decimal(str(settings.shipping_flat_amount)))
    free_threshold = Decimal(str(settings.shipping_free_threshold))
    shipping = Decimal("0.00") if free_threshold > 0 and subtotal >= free_threshold else flat_shipping
    tax_rate = Decimal(str(settings.sales_tax_percent)) / Decimal("100")
    tax = money(subtotal * tax_rate)
    total = money(subtotal + shipping + tax)
    return subtotal, shipping, tax, total


def ensure_available(product: Product, quantity: int) -> None:
    if not product.is_active:
        raise HTTPException(status_code=409, detail="This listing is currently unavailable")
    if product.inventory_quantity is not None and product.inventory_quantity < quantity:
        raise HTTPException(
            status_code=409,
            detail=f"Only {product.inventory_quantity} unit(s) are currently available",
        )


async def locked_product(db: AsyncSession, product_id: int) -> Product | None:
    return (
        await db.execute(select(Product).where(Product.id == product_id).with_for_update())
    ).scalar_one_or_none()


async def locked_order(db: AsyncSession, order_id: int) -> Order | None:
    return (
        await db.execute(select(Order).where(Order.id == order_id).with_for_update())
    ).scalar_one_or_none()


def reserve(product: Product, order: Order) -> None:
    if order.inventory_reserved:
        return
    ensure_available(product, order.quantity)
    if product.inventory_quantity is not None:
        product.inventory_quantity -= order.quantity
        order.inventory_reserved = True
    order.reservation_expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.order_reservation_minutes
    )


def release(product: Product | None, order: Order) -> None:
    if product and order.inventory_reserved and product.inventory_quantity is not None:
        product.inventory_quantity += order.quantity
    order.inventory_reserved = False
    order.reservation_expires_at = None


def consume(order: Order) -> None:
    order.inventory_reserved = False
    order.reservation_expires_at = None


async def expire_reservations(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    rows = (
        await db.execute(
            select(Order)
            .where(
                Order.status == OrderStatus.pending,
                Order.inventory_reserved.is_(True),
                Order.reservation_expires_at.is_not(None),
                Order.reservation_expires_at <= now,
            )
            .with_for_update(skip_locked=True)
        )
    ).scalars().all()
    expired = 0
    for order in rows:
        product = await locked_product(db, order.product_id)
        release(product, order)
        order.status = OrderStatus.cancelled
        order.fulfillment_status = FulfillmentStatus.cancelled
        expired += 1
    if expired:
        await db.commit()
    return expired


@router.post("/orders/quote", response_model=QuoteResponse)
async def order_quote(
    payload: QuoteRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in {Role.customer, Role.vendor}:
        raise HTTPException(status_code=403, detail="Customer or vendor account required")
    await expire_reservations(db)
    product = await db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.vendor_id == user.id:
        raise HTTPException(status_code=409, detail="Vendors cannot purchase their own product")
    ensure_available(product, payload.quantity)
    subtotal, shipping, tax, total = quote_for(product, payload.quantity)
    return QuoteResponse(
        product_id=product.id,
        quantity=payload.quantity,
        currency=product.currency,
        subtotal=subtotal,
        shipping_amount=shipping,
        tax_amount=tax,
        total=total,
    )


@router.post("/orders/checkout", response_model=CheckoutResponse, status_code=201)
async def hardened_checkout(
    payload: HardenedCheckoutRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role not in {Role.customer, Role.vendor}:
        raise HTTPException(status_code=403, detail="Customer or vendor account required")
    await expire_reservations(db)
    product = await locked_product(db, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.vendor_id == user.id:
        raise HTTPException(status_code=409, detail="Vendors cannot purchase their own product")
    ensure_available(product, payload.quantity)
    supported = {item.strip().upper() for item in settings.paystack_currencies.split(",")}
    if product.currency not in supported:
        raise HTTPException(status_code=422, detail=f"Paystack checkout is not enabled for {product.currency}")

    required = {
        "recipient_name": payload.recipient_name,
        "phone": payload.phone,
        "address_line1": payload.address_line1,
        "city": payload.city,
        "country": payload.country,
    }
    if any(not value.strip() for value in required.values()):
        raise HTTPException(status_code=422, detail="Recipient and delivery details are required")

    subtotal, shipping, tax, total = quote_for(product, payload.quantity)
    reference = f"bloom-{uuid.uuid4().hex}"
    order = Order(
        reference=reference,
        buyer_id=user.id,
        product_id=product.id,
        quantity=payload.quantity,
        unit_price=product.price,
        subtotal=subtotal,
        shipping_amount=shipping,
        tax_amount=tax,
        total=total,
        currency=product.currency,
        status=OrderStatus.pending,
        recipient_name=payload.recipient_name.strip(),
        phone=payload.phone.strip(),
        address_line1=payload.address_line1.strip(),
        city=payload.city.strip(),
        region=payload.region.strip() if payload.region else None,
        postal_code=payload.postal_code.strip() if payload.postal_code else None,
        country=payload.country.strip(),
        buyer_note=payload.buyer_note.strip() if payload.buyer_note else None,
    )
    reserve(product, order)
    db.add(order)
    await db.flush()
    try:
        data = await paystack_request(
            "POST",
            "/transaction/initialize",
            json={
                "email": user.email,
                "amount": int(total * Decimal("100")),
                "currency": product.currency,
                "reference": reference,
                "callback_url": settings.paystack_callback_url,
                "metadata": {
                    "order_id": order.id,
                    "product_id": product.id,
                    "buyer_id": user.id,
                    "subtotal": str(subtotal),
                    "shipping_amount": str(shipping),
                    "tax_amount": str(tax),
                },
            },
        )
    except HTTPException:
        await db.rollback()
        raise
    await db.commit()

    await create_notification(
        db,
        user_id=user.id,
        type="order.created",
        title="Order started",
        message=f"Your order for {product.name} is awaiting payment confirmation.",
        link="/#orders",
    )
    await create_notification(
        db,
        user_id=product.vendor_id,
        type="order.created",
        title="New order received",
        message=f"A customer started an order for {product.name} ({product.currency} {total}).",
        link="/#orders",
    )
    await notify_role(
        db,
        Role.admin,
        type="order.created",
        title="New marketplace order",
        message=f"Order #{order.id} was created for {product.name} ({product.currency} {total}).",
        link="/admin.html#activity",
        exclude_user_ids={user.id, product.vendor_id},
    )
    await db.commit()
    return CheckoutResponse(
        order_id=order.id,
        reference=reference,
        reservation_expires_at=order.reservation_expires_at,
        subtotal=subtotal,
        shipping_amount=shipping,
        tax_amount=tax,
        total=total,
        currency=product.currency,
        **data,
    )


@router.patch("/orders/{order_id}/cancel")
async def hardened_cancel(
    order_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await locked_order(db, order_id)
    if not order or order.buyer_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=409, detail="Only pending orders can be cancelled")
    product = await locked_product(db, order.product_id)
    release(product, order)
    order.status = OrderStatus.cancelled
    order.fulfillment_status = FulfillmentStatus.cancelled
    await db.commit()
    return {"id": order.id, "status": order.status.value, "fulfillment_status": order.fulfillment_status.value}


@router.post("/orders/{order_id}/pay", response_model=CheckoutResponse)
async def hardened_retry_payment(
    order_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    await expire_reservations(db)
    order = await locked_order(db, order_id)
    if not order or order.buyer_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in {OrderStatus.pending, OrderStatus.failed}:
        raise HTTPException(status_code=409, detail="This order cannot be sent for payment")
    product = await locked_product(db, order.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not order.inventory_reserved:
        reserve(product, order)
    else:
        order.reservation_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.order_reservation_minutes
        )
    reference = f"bloom-{uuid.uuid4().hex}"
    try:
        data = await paystack_request(
            "POST",
            "/transaction/initialize",
            json={
                "email": user.email,
                "amount": int(order.total * Decimal("100")),
                "currency": order.currency,
                "reference": reference,
                "callback_url": settings.paystack_callback_url,
                "metadata": {"order_id": order.id, "product_id": product.id, "buyer_id": user.id},
            },
        )
    except HTTPException:
        await db.rollback()
        raise
    order.reference = reference
    order.status = OrderStatus.pending
    order.fulfillment_status = FulfillmentStatus.unfulfilled
    await db.commit()
    return CheckoutResponse(
        order_id=order.id,
        reference=reference,
        reservation_expires_at=order.reservation_expires_at,
        subtotal=order.subtotal or money(order.unit_price * order.quantity),
        shipping_amount=order.shipping_amount,
        tax_amount=order.tax_amount,
        total=order.total,
        currency=order.currency,
        **data,
    )


@router.post("/payments/initialize", status_code=410, deprecated=True)
async def deprecated_payment_initialize():
    raise HTTPException(
        status_code=410,
        detail="This endpoint is retired. Use POST /api/v1/orders/checkout with delivery details.",
    )


@router.get("/payments/{reference}/verify")
async def hardened_verify_payment(
    reference: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    order = (
        await db.execute(select(Order).where(Order.reference == reference).with_for_update())
    ).scalar_one_or_none()
    if not order or (user.role != Role.admin and order.buyer_id != user.id):
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatus.paid:
        data = await paystack_request("GET", f"/transaction/verify/{reference}")
        from .main import settle_order

        order = await settle_order(reference, data, db)
    if order.status == OrderStatus.paid and order.inventory_reserved:
        consume(order)
        await db.commit()
    return {
        "id": order.id,
        "reference": order.reference,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "unit_price": order.unit_price,
        "total": order.total,
        "currency": order.currency,
        "status": order.status.value,
        "created_at": order.created_at,
        "paid_at": order.paid_at,
    }


@router.patch("/orders/{order_id}/fulfillment")
async def hardened_fulfillment(
    order_id: int,
    payload: FulfillmentUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await locked_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    product = await locked_product(db, order.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if user.role not in {Role.vendor, Role.admin} or (user.role == Role.vendor and product.vendor_id != user.id):
        raise HTTPException(status_code=403, detail="Vendor access required")
    if order.status != OrderStatus.paid:
        raise HTTPException(status_code=409, detail="Only paid orders can be fulfilled")
    if order.refund_status in {RefundStatus.processing, RefundStatus.refunded}:
        raise HTTPException(status_code=409, detail="Refunded orders cannot be fulfilled")
    if payload.status == FulfillmentStatus.cancelled:
        raise HTTPException(status_code=409, detail="Paid orders use the refund workflow rather than fulfillment cancellation")
    if payload.status == FulfillmentStatus.shipped and (not payload.carrier or not payload.tracking_number):
        raise HTTPException(status_code=422, detail="Carrier and tracking number are required when marking an order shipped")
    allowed = {
        FulfillmentStatus.unfulfilled: {FulfillmentStatus.processing, FulfillmentStatus.shipped},
        FulfillmentStatus.processing: {FulfillmentStatus.shipped},
        FulfillmentStatus.shipped: {FulfillmentStatus.delivered},
        FulfillmentStatus.delivered: set(),
        FulfillmentStatus.cancelled: set(),
    }
    if payload.status != order.fulfillment_status and payload.status not in allowed[order.fulfillment_status]:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot move fulfillment from {order.fulfillment_status.value} to {payload.status.value}",
        )
    order.fulfillment_status = payload.status
    now = datetime.now(timezone.utc)
    if payload.status == FulfillmentStatus.shipped:
        order.carrier = payload.carrier.strip()
        order.tracking_number = payload.tracking_number.strip()
        order.shipped_at = now
        registration = await register_tracking(
            tracking_number=order.tracking_number,
            order_id=order.id,
            carrier=order.carrier,
        )
        if registration:
            order.tracking_provider_id = str(registration.get("id") or "") or None
            order.tracking_status = str(registration.get("tag") or registration.get("status") or "registered")
        else:
            order.tracking_status = "manual" if not settings.aftership_enabled else "registration_failed"
        order.tracking_updated_at = now
    elif payload.status == FulfillmentStatus.delivered:
        order.delivered_at = now
        order.tracking_status = "Delivered"
        order.tracking_updated_at = now
    await create_notification(
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
        "shipped_at": order.shipped_at,
        "delivered_at": order.delivered_at,
    }


async def reconcile_refund(event: str, data: dict, db: AsyncSession) -> None:
    reference = str(data.get("transaction_reference") or "")
    if not reference:
        return
    order = (
        await db.execute(select(Order).where(Order.reference == reference).with_for_update())
    ).scalar_one_or_none()
    if not order:
        return
    amount = data.get("amount")
    currency = data.get("currency")
    if amount is not None:
        try:
            if int(Decimal(str(amount))) != int(order.total * Decimal("100")):
                raise HTTPException(status_code=422, detail="Refund amount does not match the order")
        except (ValueError, ArithmeticError):
            raise HTTPException(status_code=422, detail="Invalid refund amount")
    if currency and str(currency).upper() != order.currency:
        raise HTTPException(status_code=422, detail="Refund currency does not match the order")

    previous = (order.refund_status, order.refund_provider_status)
    order.refund_provider_status = event
    order.refund_reference = str(data.get("refund_reference") or "") or order.refund_reference
    if event == "refund.processed":
        order.refund_status = RefundStatus.refunded
        order.refund_processed_at = datetime.now(timezone.utc)
    elif event in {"refund.pending", "refund.processing"}:
        order.refund_status = RefundStatus.processing
    elif event in {"refund.failed", "refund.needs-attention"}:
        order.refund_status = RefundStatus.approved
    if previous != (order.refund_status, order.refund_provider_status):
        product = await db.get(Product, order.product_id)
        await create_notification(
            db,
            user_id=order.buyer_id,
            type="payment.refund_update",
            title="Refund update",
            message=f"Refund for order #{order.id}: {event.replace('refund.', '').replace('-', ' ')}.",
            link="/#orders",
        )
        if product:
            await create_notification(
                db,
                user_id=product.vendor_id,
                type="order.refund_update",
                title="Refund update",
                message=f"Refund for order #{order.id}: {event.replace('refund.', '').replace('-', ' ')}.",
                link="/#orders",
            )
    await db.commit()


@router.post("/payments/webhook", include_in_schema=False)
async def hardened_paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    if not valid_webhook_signature(payload, request.headers.get("x-paystack-signature")):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    body = await request.json()
    event = str(body.get("event") or "")
    data = body.get("data", {})
    if event == "charge.success":
        from .main import settle_order

        try:
            order = await settle_order(data.get("reference", ""), data, db)
            if order.status == OrderStatus.paid and order.inventory_reserved:
                consume(order)
                await db.commit()
        except HTTPException as error:
            if error.status_code != 404:
                raise
    elif event in {
        "refund.pending",
        "refund.processing",
        "refund.needs-attention",
        "refund.failed",
        "refund.processed",
    }:
        await reconcile_refund(event, data, db)
    return {"status": "accepted"}


@router.post("/shipping/aftership/webhook", include_in_schema=False)
async def aftership_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    if not valid_aftership_signature(payload, request.headers.get("aftership-hmac-sha256")):
        raise HTTPException(status_code=401, detail="Invalid tracking webhook signature")
    body = await request.json()
    if body.get("event") not in {"tracking_update", "edd_revise", "tracking_pending_time"}:
        return {"status": "accepted"}
    msg = body.get("msg") or {}
    tracking_number = str(msg.get("tracking_number") or "")
    provider_id = str(msg.get("id") or "")
    query = select(Order)
    if provider_id:
        query = query.where(Order.tracking_provider_id == provider_id)
    elif tracking_number:
        query = query.where(Order.tracking_number == tracking_number)
    else:
        return {"status": "accepted"}
    order = (await db.execute(query.with_for_update())).scalar_one_or_none()
    if not order:
        return {"status": "accepted"}
    tag = str(msg.get("tag") or msg.get("status") or "updated")
    changed = tag != order.tracking_status
    order.tracking_status = tag
    order.tracking_updated_at = datetime.now(timezone.utc)
    if tag.lower().replace(" ", "") == "delivered" and order.status == OrderStatus.paid:
        order.fulfillment_status = FulfillmentStatus.delivered
        order.delivered_at = datetime.now(timezone.utc)
    if changed:
        await create_notification(
            db,
            user_id=order.buyer_id,
            type="order.tracking_update",
            title="Shipment update",
            message=f"Tracking update for order #{order.id}: {tag}.",
            link="/#orders",
        )
    await db.commit()
    return {"status": "accepted"}
