import json, logging, os, uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from redis.asyncio import Redis
from .schemas import AdverseEventRequest, FeedbackRequest
from .queue import enqueue_case, get_case, QUEUE_NAME
from .metrics import REQUESTS, RUNS_SUBMITTED
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(message)s")
logger = logging.getLogger("pharmasafe")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
app = FastAPI(title="PharmaSafe AI API", version="0.1.0",
              description="Adverse-event intake and triage decision-support service. Not a regulatory submission system.")
redis: Redis | None = None

@app.on_event("startup")
async def startup():
    global redis
    redis = Redis.from_url(REDIS_URL, decode_responses=False)
    await redis.ping()

@app.on_event("shutdown")
async def shutdown():
    if redis:
        await redis.aclose()

@app.middleware("http")
async def request_logging(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    REQUESTS.labels(request.url.path, request.method, str(response.status_code)).inc()
    logger.info(json.dumps({"event":"http_request","correlation_id":correlation_id,
                            "method":request.method,"path":request.url.path,
                            "status":response.status_code}))
    return response

@app.get("/")
async def root():
    return {"service":"PharmaSafe AI API","docs":"/docs","health":"/health"}

@app.get("/health")
async def health():
    try:
        await redis.ping()
        return {"status":"healthy","redis":"connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Redis unavailable")

@app.post("/api/v1/cases", status_code=202)
async def submit_case(case: AdverseEventRequest):
    # Pydantic validation happens before this function; malformed requests never enter the queue.
    payload = case.model_dump(mode="json")
    await enqueue_case(redis, case.case_id, payload)
    RUNS_SUBMITTED.inc()
    logger.info(json.dumps({"event":"case_queued","case_id":case.case_id}))
    return {"case_id":case.case_id,"status":"queued",
            "status_url":f"/api/v1/cases/{case.case_id}"}

@app.get("/api/v1/cases/{case_id}")
async def case_status(case_id: str):
    item = await get_case(redis, case_id)
    if not item:
        raise HTTPException(status_code=404, detail="Case not found")
    return item

@app.post("/api/v1/cases/{case_id}/feedback", status_code=201)
async def feedback(case_id: str, body: FeedbackRequest):
    item = await get_case(redis, case_id)
    if not item:
        raise HTTPException(status_code=404, detail="Case not found")
    await redis.lpush("pharmasafe:feedback", json.dumps({
        "case_id":case_id, **body.model_dump(),
        "created_at":datetime.now(timezone.utc).isoformat()
    }))
    return {"saved":True,"case_id":case_id}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
