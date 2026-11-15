import json
from redis.asyncio import Redis

QUEUE_NAME = "pharmasafe:case_queue"

async def enqueue_case(redis: Redis, case_id: str, payload: dict):
    await redis.hset(f"pharmasafe:case:{case_id}", mapping={
        "status": "queued",
        "created_at": __import__("datetime").datetime.utcnow().isoformat(),
        "result": "",
        "error": "",
    })
    await redis.lpush(QUEUE_NAME, json.dumps({"case_id": case_id, "payload": payload}))

async def get_case(redis: Redis, case_id: str):
    data = await redis.hgetall(f"pharmasafe:case:{case_id}")
    if not data:
        return None
    decoded = {k.decode(): v.decode() for k, v in data.items()}
    if decoded.get("result"):
        decoded["result"] = json.loads(decoded["result"])
    return decoded
