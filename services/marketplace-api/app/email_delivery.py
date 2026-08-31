from __future__ import annotations

import html
import logging

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_transactional_email(
    *,
    to: str,
    subject: str,
    message: str,
    link: str | None = None,
) -> bool:
    """Send a transactional email when Resend is configured.

    Delivery is best-effort: notification persistence must never fail because the
    external email provider is unavailable.
    """
    if not settings.transactional_email_enabled:
        return False

    safe_subject = html.escape(subject)
    safe_message = html.escape(message)
    action = ""
    if link:
        url = link if link.startswith("http") else f"{settings.web_base_url.rstrip('/')}{link}"
        safe_url = html.escape(url, quote=True)
        action = f'<p><a href="{safe_url}">Open BloomAI</a></p>'

    payload = {
        "from": settings.resend_from_email,
        "to": [to],
        "subject": subject,
        "html": (
            "<div style=\"font-family:Arial,sans-serif;max-width:600px;margin:auto\">"
            f"<h2>{safe_subject}</h2><p>{safe_message}</p>{action}"
            "<p style=\"color:#667085;font-size:12px\">"
            "You received this transactional message because email notifications are enabled in BloomAI."
            "</p></div>"
        ),
        "text": f"{subject}\n\n{message}",
    }
    if link:
        payload["text"] += f"\n\nOpen BloomAI: {url}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
        return True
    except (httpx.HTTPError, ValueError):
        logger.exception("Transactional email delivery failed for recipient")
        return False
