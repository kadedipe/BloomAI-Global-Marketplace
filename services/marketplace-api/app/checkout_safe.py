from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from . import hardening
from .database import get_db
from .models import Order, OrderStatus, Role, User
from .security import current_user

logger = logging.getLogger(__name__)


async def hardened_checkout(
    payload: hardening.HardenedCheckoutRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
) -> hardening.CheckoutResponse:
    """Create a checkout without letting post-commit side effects destroy the response.

    Order creation, inventory reservation, and Paystack initialization are the authoritative
    transaction. Notifications are deliberately best-effort after that transaction commits.
    """
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
    except HTTPException:
        await db.rollback()
        raise
    except Exception:
        await db.rollback()
        logger.exception("Unexpected checkout provider failure before order commit")
        raise HTTPException(
            status_code=502, detail="Payment provider initialization failed"
        )

    # Commit the authoritative commerce state before optional notification delivery.
    await db.commit()

    # Build the response immediately from committed state and provider data. From this point
    # onward, notification/email failures must never make the browser believe checkout failed.
    response = hardening.CheckoutResponse(
        order_id=order.id,
        reference=reference,
        reservation_expires_at=order.reservation_expires_at,
        subtotal=subtotal,
        shipping_amount=shipping,
        tax_amount=tax,
        total=total,
        currency=product.currency,
        **provider_data,
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
