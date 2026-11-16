
from prometheus_client import start_http_server
import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone

from redis.asyncio import Redis

from app.agent_adapter import run_agent
from app.queue import QUEUE_NAME
from app.metrics import (
    RUNS_COMPLETED,
    RUNS_FAILED,
    RUN_LATENCY,
    QUEUE_DEPTH,
)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(message)s",
)

log = logging.getLogger("pharmasafe-worker")


async def process(redis: Redis, item: dict):
    case_id = item["case_id"]
    payload = item["payload"]
    correlation_id = payload.get("_correlation_id", "")

    key = f"pharmasafe:case:{case_id}"
    start = time.perf_counter()

    await redis.hset(key, mapping={"status": "processing", "correlation_id": correlation_id})

    try:
        result = await asyncio.wait_for(
            run_agent(payload),
            timeout=int(os.getenv("CASE_TIMEOUT_SECONDS", "90")),
        )

        await redis.hset(
            key,
            mapping={
                "status": "completed",
                "result": json.dumps(result),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        RUNS_COMPLETED.inc()

        log.info(
            json.dumps({
                "event": "case_completed",
                "case_id": case_id,
                "correlation_id": correlation_id,
            })
        )

    except Exception as exc:
        await redis.hset(
            key,
            mapping={
                "status": "failed",
                "error": str(exc)[:500],
                "correlation_id": correlation_id,
            },
        )

        RUNS_FAILED.inc()
        log.exception("case_failed case_id=%s correlation_id=%s", case_id, correlation_id)

    finally:
        RUN_LATENCY.observe(time.perf_counter() - start)
        QUEUE_DEPTH.set(await redis.llen(QUEUE_NAME))


async def main():
    redis = Redis.from_url(
        os.getenv("REDIS_URL", "redis://redis:6379/0"),
        decode_responses=True,
    )

    try:
        await redis.ping()
        log.info("Redis connection established.")

        while True:
            try:
                QUEUE_DEPTH.set(await redis.llen(QUEUE_NAME))

                popped = await redis.brpop(QUEUE_NAME, timeout=5)

                if popped:
                    _, raw = popped
                    QUEUE_DEPTH.set(await redis.llen(QUEUE_NAME))

                    await process(redis, json.loads(raw))

            except Exception:
                log.exception("worker_loop_error")
                await asyncio.sleep(2)

    finally:
        await redis.aclose()


if __name__ == "__main__":
    start_http_server(8001)
    asyncio.run(main())
