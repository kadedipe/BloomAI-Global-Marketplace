import json
import logging
from datetime import datetime, timezone
from redis.asyncio import Redis
from .config import get_settings

logger = logging.getLogger(__name__)
QUEUE_NAME = "bloomai:events"


async def publish_event(name: str, payload: dict) -> None:
    """Publish a domain event without making the request depend on the worker."""
    event = {
        "name": name,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "schema_version": 1,
    }
    client = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        await client.lpush(QUEUE_NAME, json.dumps(event))
    except Exception:
        logger.exception("domain_event_publish_failed", extra={"event_name": name})
    finally:
        await client.aclose()
