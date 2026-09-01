import asyncio
import json
import logging
import os
import signal
import time

import asyncpg
from redis import Redis

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("bloomai.event_worker")
QUEUE_NAME = "bloomai:events"
CLEANUP_INTERVAL_SECONDS = int(os.getenv("RESERVATION_CLEANUP_INTERVAL_SECONDS", "60"))
running = True


def stop(*_args):
    global running
    running = False


def process(raw_event: str) -> None:
    """Handle versioned domain events behind a provider-independent boundary."""
    event = json.loads(raw_event)
    logger.info(
        "domain_event_processed name=%s schema_version=%s payload=%s",
        event.get("name"),
        event.get("schema_version"),
        json.dumps(event.get("payload", {}), sort_keys=True),
    )


def asyncpg_url(value: str) -> str:
    return value.replace("postgresql+asyncpg://", "postgresql://", 1).replace(
        "postgres+asyncpg://", "postgresql://", 1
    )


async def expire_reservations(database_url: str) -> int:
    connection = await asyncpg.connect(asyncpg_url(database_url))
    expired = 0
    try:
        async with connection.transaction():
            rows = await connection.fetch(
                """
                SELECT id, product_id, quantity
                FROM orders
                WHERE status = 'pending'
                  AND inventory_reserved = TRUE
                  AND reservation_expires_at IS NOT NULL
                  AND reservation_expires_at <= NOW()
                FOR UPDATE SKIP LOCKED
                LIMIT 100
                """
            )
            for row in rows:
                await connection.execute(
                    """
                    UPDATE products
                    SET inventory_quantity = CASE
                        WHEN inventory_quantity IS NULL THEN NULL
                        ELSE inventory_quantity + $1
                    END
                    WHERE id = $2
                    """,
                    row["quantity"],
                    row["product_id"],
                )
                await connection.execute(
                    """
                    UPDATE orders
                    SET status = 'cancelled',
                        fulfillment_status = 'cancelled',
                        inventory_reserved = FALSE,
                        reservation_expires_at = NULL
                    WHERE id = $1
                    """,
                    row["id"],
                )
                expired += 1
    finally:
        await connection.close()
    return expired


def main() -> None:
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    client = Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    database_url = os.getenv("DATABASE_URL", "")
    next_cleanup = 0.0
    if not database_url:
        logger.warning("reservation_cleanup_disabled reason=DATABASE_URL_missing")
    logger.info("event_worker_started queue=%s", QUEUE_NAME)
    while running:
        if database_url and time.monotonic() >= next_cleanup:
            try:
                expired = asyncio.run(expire_reservations(database_url))
                if expired:
                    logger.info("inventory_reservations_expired count=%s", expired)
            except (asyncpg.PostgresError, OSError, ValueError):
                logger.exception("inventory_reservation_cleanup_failed")
            next_cleanup = time.monotonic() + CLEANUP_INTERVAL_SECONDS
        item = client.brpop(QUEUE_NAME, timeout=5)
        if not item:
            continue
        try:
            process(item[1])
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.exception("invalid_domain_event")
    client.close()


if __name__ == "__main__":
    main()
