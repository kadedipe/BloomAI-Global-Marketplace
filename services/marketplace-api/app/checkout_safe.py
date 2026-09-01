from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from . import hardening
from .database import get_db
from .models import FulfillmentStatus, Order, OrderStatus, Role, User
from .security import current_user

logger = logging.getLogger(__name__)


def provider_checkout_fields(provider_data: dict) -> tuple[str, str]:
    """Extract only the Paystack fields BloomAI exposes to the browser.

    Paystack also returns its own `reference`. BloomAI owns the canonical order reference,
    so blindly expanding provider data into CheckoutResponse can pass `reference` twice and
    raise a TypeError after the database transaction has already committed.
    """
    authorization_url = provider_data.get("authorization_url")
    access_code = provider_data.get("access_code")
    if not isinstance(authorization_url, str) or not authorization_url:
        raise HTTPException(
            status_code=502, detail="Payment provider returned no authorization URL"
        )
    if not isinstance(access_code, str) or not access_code:
        raise HTTPException(
            status_code=502, detail="Payment provider returned no checkout access code"
        )
    return authorization_url, access_code


async def hardened_checkout(
    payload: hardening.HardenedCheckoutRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> hardening.CheckoutResponse:
    """Create a checkout without letting post-commit side effects destroy the response."""
    if user.role not in {Role.customer, Role.vendor}:
        raise HTTPException(status_code=403, detail="Customer or vendor account required")

    await hardening.expire_reservations(db)
    product = await hardening.locked_product(db, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.vendor_id == user.id:
        raise HTTPException(status_code=409, detail="Vendors cannot purchase their own product")
    hardening.ensure_available(product, payload.quantity)

    supported = {
        item.strip().upper() for item in hardening.settings.paystack_currencies.split(",")
    }
    if product.currency not in supported:
        raise HTTPException(
            status_code=422,
            detail=f"Paystack checkout is not enabled for {product.currency}",
        )

    required = {
        "recipient_name": payload.recipient_name,
        "phone": payload.phone,
        "address_line1": payload.address_line1,
        "city": payload.city,
        "country": payload.country,
    }
    if any(not value.strip() for value in required.values()):
        raise HTTPException(
            status_code=422, detail="Recipient and delivery details are required"
        )

    subtotal, shipping, tax, total = hardening.quote_for(product, payload.quantity)
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
    hardening.reserve(product, order)
    db.add(order)
    await db.flush()

    try:
        provider_data = await hardening.paystack_request(
            "POST",
            "/transaction/initialize",
            json={
                "email": user.email,
                "amount": int(total * Decimal("100")),
                "currency": product.currency,
                "reference": reference,
                "callback_url": hardening.settings.paystack_callback_url,
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
        authorization_url, access_code = provider_checkout_fields(provider_data)
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        logger.exception("Unexpected checkout provider failure before order commit")
        raise HTTPException(
            status_code=502, detail="Payment provider initialization failed"
        )

    await db.commit()

    response = hardening.CheckoutResponse(
        order_id=order.id,
        reference=reference,
        authorization_url=authorization_url,
        access_code=access_code,
        reservation_expires_at=order.reservation_expires_at,
        subtotal=subtotal,
        shipping_amount=shipping,
        tax_amount=tax,
        total=total,
        currency=product.currency,
    )

    try:
        await hardening.create_notification(
            db,
            user_id=user.id,
            type="order.created",
            title="Order started",
            message=f"Your order for {product.name} is awaiting payment confirmation.",
            link="/#orders",
        )
        await hardening.create_notification(
            db,
            user_id=product.vendor_id,
            type="order.created",
            title="New order received",
            message=(
                f"A customer started an order for {product.name} "
                f"({product.currency} {total})."
            ),
            link="/#orders",
        )
        await hardening.notify_role(
            db,
            Role.admin,
            type="order.created",
            title="New marketplace order",
            message=(
                f"Order #{order.id} was created for {product.name} "
                f"({product.currency} {total})."
            ),
            link="/admin.html#activity",
            exclude_user_ids={user.id, product.vendor_id},
        )
        await db.commit()
    except Exception:
        await db.rollback()
        logger.exception(
            "Checkout order %s committed, but notification delivery failed", order.id
        )

    return response


async def hardened_retry_payment(
    order_id: int,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> hardening.CheckoutResponse:
    """Initialize Paystack for an existing order without duplicating provider fields."""
    await hardening.expire_reservations(db)
    order = await hardening.locked_order(db, order_id)
    if not order or order.buyer_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in {OrderStatus.pending, OrderStatus.failed}:
        raise HTTPException(status_code=409, detail="This order cannot be sent for payment")

    product = await hardening.locked_product(db, order.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not order.inventory_reserved:
        hardening.reserve(product, order)
    else:
        order.reservation_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=hardening.settings.order_reservation_minutes
        )

    reference = f"bloom-{uuid.uuid4().hex}"
    try:
        provider_data = await hardening.paystack_request(
            "POST",
            "/transaction/initialize",
            json={
                "email": user.email,
                "amount": int(order.total * Decimal("100")),
                "currency": order.currency,
                "reference": reference,
                "callback_url": hardening.settings.paystack_callback_url,
                "metadata": {
                    "order_id": order.id,
                    "product_id": product.id,
                    "buyer_id": user.id,
                },
            },
        )
        authorization_url, access_code = provider_checkout_fields(provider_data)
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        logger.exception("Unexpected retry-payment provider failure")
        raise HTTPException(
            status_code=502, detail="Payment provider initialization failed"
        )

    order.reference = reference
    order.status = OrderStatus.pending
    order.fulfillment_status = FulfillmentStatus.unfulfilled
    await db.commit()

    return hardening.CheckoutResponse(
        order_id=order.id,
        reference=reference,
        authorization_url=authorization_url,
        access_code=access_code,
        reservation_expires_at=order.reservation_expires_at,
        subtotal=order.subtotal or hardening.money(order.unit_price * order.quantity),
        shipping_amount=order.shipping_amount,
        tax_amount=order.tax_amount,
        total=order.total,
        currency=order.currency,
    )
