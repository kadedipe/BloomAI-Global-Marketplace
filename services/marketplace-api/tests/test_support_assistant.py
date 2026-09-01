import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from app.models import Role
from app.support_assistant import classify_message, fallback_reply


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
