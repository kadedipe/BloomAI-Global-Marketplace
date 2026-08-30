import json
import logging
import os
import signal
from redis import Redis

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("bloomai.event_worker")
QUEUE_NAME = "bloomai:events"
running = True

def stop(*_args):
    global running
    running = False

def process(raw_event: str) -> None:
    """Handle versioned domain events behind a provider-independent boundary."""
    event = json.loads(raw_event)
    logger.info("domain_event_processed name=%s schema_version=%s payload=%s", event.get("name"), event.get("schema_version"), json.dumps(event.get("payload", {}), sort_keys=True))

def main() -> None:
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    client = Redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
    logger.info("event_worker_started queue=%s", QUEUE_NAME)
    while running:
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
