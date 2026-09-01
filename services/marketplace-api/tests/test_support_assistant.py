import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.models import Role
from app.support_assistant import (
    classify_message,
    critical_reply,
    fallback_reply,
    safe_ai_output,
)


def test_critical_payment_issue_recommends_escalation():
    category, critical = classify_message("I was charged twice for my order")
    assert category == "payment"
    assert critical is True


def test_refund_issue_is_classified_without_automatic_action():
    category, critical = classify_message("Where is my refund?")
    assert category == "refund"
    assert critical is False
    reply = fallback_reply(category, "Order #6: refund=processing.", critical)
    assert "refund" in reply.lower()
    assert "Order #6" in reply


def test_account_safety_message_never_requests_password():
    category, critical = classify_message("I need help with my account login")
    assert category == "account"
    reply = fallback_reply(category, "No marketplace orders are available for this account.", critical)
    assert "never ask for your password" in reply.lower()


def test_role_enum_keeps_customer_and_vendor_scope():
    assert Role.customer.value == "customer"
    assert Role.vendor.value == "vendor"


def test_reasoning_style_provider_output_is_rejected():
    leaked = (
        "Here's a thinking process:\n"
        "1. Analyze User Input\n"
        "2. Key observations: order #6 was refunded"
    )
    assert safe_ai_output(leaked) is None


def test_normal_support_answer_is_kept_and_markdown_is_removed():
    answer = "**Payment:** Paid\n- Refund: Refunded"
    cleaned = safe_ai_output(answer)
    assert cleaned == "Payment: Paid\n- Refund: Refunded"


def test_critical_reply_only_directs_to_bloomai_admin_contact():
    reply = critical_reply(
        "payment",
        "Order #6: payment=paid, fulfillment=delivered, refund=refunded.",
    )
    lowered = reply.lower()
    assert "bloomai administrator/support contact" in lowered
    assert "security team" not in lowered
    assert "chargeback" not in lowered
    assert "investigation" not in lowered
    assert "order #6" in lowered


def test_fallback_critical_reply_uses_deterministic_path():
    reply = fallback_reply(
        "account",
        "No marketplace orders are available for this account.",
        True,
    )
    assert "unauthorized account access" in reply.lower()
    assert "bloomai administrator/support contact" in reply.lower()
