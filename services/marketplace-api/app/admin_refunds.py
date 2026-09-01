from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import Order, Product, RefundStatus, Role, User
from .security import current_user

router = APIRouter(prefix="/admin/commerce", tags=["admin-commerce"])


@router.get("/refunds")
async def refund_queue(
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Administrator access required")

    orders = (
        await db.execute(
            select(Order)
            .where(
                Order.refund_status.in_(
                    {
                        RefundStatus.requested,
                        RefundStatus.approved,
                        RefundStatus.processing,
                        RefundStatus.refunded,
                    }
                )
            )
            .order_by(Order.refund_requested_at.desc(), Order.id.desc())
        )
    ).scalars().all()

    rows = []
    for order in orders:
        product = await db.get(Product, order.product_id)
        buyer = await db.get(User, order.buyer_id)
        rows.append(
            {
                "order_id": order.id,
                "reference": order.reference,
                "product_name": product.name if product else "Unknown product",
                "buyer_name": buyer.name if buyer else "Customer",
                "amount": order.total,
                "currency": order.currency,
                "refund_status": order.refund_status.value,
                "refund_reason": order.refund_reason,
                "refund_provider_status": order.refund_provider_status,
                "refund_requested_at": order.refund_requested_at,
                "refund_processed_at": order.refund_processed_at,
                "can_execute": (
                    order.refund_status == RefundStatus.approved
                    and bool(order.provider_transaction_id)
                ),
            }
        )
    return {"items": rows}
