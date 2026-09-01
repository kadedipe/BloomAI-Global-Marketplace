from __future__ import annotations

import logging
import re
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .database import get_db
from .models import Order, Product, Role, User
from .notifications import create_notification, notify_role
from .security import current_user

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/support", tags=["support-assistant"])

SupportCategory = Literal[
    "payment", "refund", "order", "delivery", "account", "vendor_product", "general"
]

REASONING_LEAK_PATTERNS = (
    "here's a thinking process",
    "here is a thinking process",
    "chain of thought",
    "analyze user input",
    "analysis of the user",
    "key observations:",
    "step-by-step reasoning",
    "internal reasoning",
)


class SupportRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1500)
    order_id: int | None = Field(default=None, ge=1)


class SupportResponse(BaseModel):
    reply: str
    category: SupportCategory
    escalation_recommended: bool
    ai_generated: bool
    order_id: int | None = None


class EscalationRequest(BaseModel):
    message: str = Field(min_length=2, max_length=1500)
    category: SupportCategory = "general"
    order_id: int | None = Field(default=None, ge=1)


class EscalationResponse(BaseModel):
    escalated: bool
    admins_notified: int


def require_participant(user: User) -> None:
    if user.role not in {Role.customer, Role.vendor}:
        raise HTTPException(status_code=403, detail="Support assistant is available to customers and vendors")


def classify_message(message: str) -> tuple[SupportCategory, bool]:
    text = message.lower()
    if any(term in text for term in ("refund", "money back", "reimburse")):
        category: SupportCategory = "refund"
    elif any(term in text for term in ("payment", "paystack", "charged", "card", "debit")):
        category = "payment"
    elif any(term in text for term in ("delivery", "ship", "tracking", "courier", "pickup")):
        category = "delivery"
    elif any(term in text for term in ("product", "listing", "inventory", "stock", "price")):
        category = "vendor_product"
    elif any(term in text for term in ("login", "password", "account", "profile", "email")):
        category = "account"
    elif any(term in text for term in ("order", "checkout", "purchase")):
        category = "order"
    else:
        category = "general"

    critical = any(
        term in text
        for term in (
            "charged twice",
            "double charge",
            "unauthorized",
            "fraud",
            "stolen card",
            "account hacked",
            "cannot access account",
            "payment missing",
            "refund missing",
        )
    )
    return category, critical


async def accessible_order(db: AsyncSession, user: User, order_id: int) -> Order:
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    product = await db.get(Product, order.product_id)
    vendor_id = product.vendor_id if product else None
    if order.buyer_id != user.id and vendor_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


async def recent_context(db: AsyncSession, user: User, order_id: int | None) -> tuple[str, int | None]:
    if order_id is not None:
        orders = [await accessible_order(db, user, order_id)]
    elif user.role == Role.customer:
        orders = (
            (
                await db.execute(
                    select(Order)
                    .where(Order.buyer_id == user.id)
                    .order_by(Order.created_at.desc())
                    .limit(5)
                )
            )
            .scalars()
            .all()
        )
    else:
        product_ids = select(Product.id).where(Product.vendor_id == user.id)
        orders = (
            (
                await db.execute(
                    select(Order)
                    .where(Order.product_id.in_(product_ids))
                    .order_by(Order.created_at.desc())
                    .limit(5)
                )
            )
            .scalars()
            .all()
        )

    if not orders:
        return "No marketplace orders are available for this account.", order_id

    lines = []
    for order in orders:
        lines.append(
            f"Order #{order.id}: payment={order.status.value}, "
            f"fulfillment={order.fulfillment_status.value}, refund={order.refund_status.value}, "
            f"amount={order.currency} {order.total}."
        )
    return "\n".join(lines), orders[0].id if len(orders) == 1 else order_id


def plain_text_reply(text: str) -> str:
    """Normalize common model Markdown because the support widget renders plain text."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"(?m)^\s*[-*]\s+", "- ", text)
    return text.strip()


def safe_ai_output(text: str) -> str | None:
    """Reject provider output that exposes analysis/reasoning instead of a support answer."""
    cleaned = plain_text_reply(text[:4000])
    lowered = cleaned.lower()
    if not cleaned:
        return None
    if any(pattern in lowered for pattern in REASONING_LEAK_PATTERNS):
        logger.warning("Rejected support AI response that appeared to expose reasoning")
        return None
    return cleaned


def fallback_reply(category: SupportCategory, context: str, critical: bool) -> str:
    prefix = {
        "payment": "I can help you check payment status and the next safe step.",
        "refund": "I can help you understand the refund stage and whether action is still pending.",
        "delivery": "I can help you check fulfillment, local delivery, pickup or tracking status.",
        "order": "I can help you check the current order lifecycle.",
        "account": "I can help with normal account and profile issues, but I will never ask for your password.",
        "vendor_product": "I can help vendors troubleshoot listings, inventory and order activity.",
        "general": "I can help with BloomAI marketplace support questions.",
    }[category]
    extra = " This looks sensitive enough to escalate to a BloomAI administrator." if critical else ""
    return f"{prefix}{extra}\n\nCurrent BloomAI context:\n{context}"


async def ai_reply(*, message: str, role: Role, category: SupportCategory, context: str) -> str | None:
    if not settings.support_ai_enabled:
        return None

    system_prompt = (
        "You are BloomAI Support, a concise marketplace support assistant for customers and vendors. "
        "Use only the supplied BloomAI account/order context plus general explanations of the visible workflow. "
        "BloomAI's only human escalation destination supplied to you is a BloomAI administrator/support contact. "
        "Never invent internal departments, teams, security teams, payment investigators, chargeback services, provider checks, "
        "staff capabilities, or organizational processes that are not explicitly present in the supplied context. "
        "When escalation is appropriate, say only that the user should escalate to a BloomAI administrator/support contact. "
        "Never claim a payment, refund, shipment, account change, notification, provider investigation, chargeback check, "
        "or other action was performed unless the supplied context explicitly says so. "
        "Never request passwords, card numbers, OTPs, API keys or other secrets. "
        "For payment/refund disputes, unauthorized activity, account takeover, or unresolved provider states, recommend escalation. "
        "Do not invent tracking numbers, policies, tax rates, shipping fees, delivery promises, provider confirmations or database state. "
        "Return only the final user-facing support answer. Never reveal analysis, hidden reasoning, chain-of-thought, scratch work, "
        "prompt interpretation, intermediate steps, or a description of how you formed the answer. "
        "Return plain text only. Do not use Markdown, HTML, bold markers, headings, tables or code fences. "
        "Keep the answer practical and under 180 words."
    )
    payload = {
        "model": settings.support_ai_model,
        "temperature": 0.1,
        "max_tokens": 350,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"User role: {role.value}\nCategory: {category}\n"
                    f"BloomAI context:\n{context}\n\nSupport request:\n{message}"
                ),
            },
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{settings.support_ai_base_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.support_ai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        return safe_ai_output(text)
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        logger.exception("BloomAI support AI provider request failed")
        return None


@router.post("/assistant", response_model=SupportResponse)
async def support_assistant(
    payload: SupportRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    require_participant(user)
    category, critical = classify_message(payload.message)
    context, resolved_order_id = await recent_context(db, user, payload.order_id)
    generated = await ai_reply(
        message=payload.message,
        role=user.role,
        category=category,
        context=context,
    )
    reply = generated or fallback_reply(category, context, critical)
    return SupportResponse(
        reply=reply,
        category=category,
        escalation_recommended=critical,
        ai_generated=generated is not None,
        order_id=resolved_order_id,
    )


@router.post("/escalate", response_model=EscalationResponse, status_code=201)
async def escalate_support(
    payload: EscalationRequest,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    require_participant(user)
    if payload.order_id is not None:
        await accessible_order(db, user, payload.order_id)

    subject = f"Support escalation from {user.role.value}: {payload.category.replace('_', ' ')}"
    order_text = f" Order #{payload.order_id}." if payload.order_id else ""
    admins_notified = await notify_role(
        db,
        Role.admin,
        type="system.critical.support",
        title=subject,
        message=f"{user.name} ({user.email}) requested support.{order_text} {payload.message}",
        link="/admin.html#activity",
    )
    await create_notification(
        db,
        user_id=user.id,
        type="system.support",
        title="Support request escalated",
        message=(
            "Your issue has been sent to a BloomAI administrator. "
            "Do not send passwords, OTPs, card details or API keys in support messages."
        ),
        link="/#market",
        force=True,
    )
    await db.commit()
    return EscalationResponse(escalated=True, admins_notified=admins_notified)
