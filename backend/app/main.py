import json, logging, os, uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Correlation-ID"],
)
redis: Redis | None = None


@app.exception_handler(RequestValidationError)
async def quarantine_invalid_request(request: Request, exc: RequestValidationError):
    """Record field-level rejection metadata without retaining free-text case data."""
    correlation_id = getattr(request.state, "correlation_id", None) or request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    errors = [{"field": ".".join(str(part) for part in item.get("loc", ())[1:]),
               "message": item.get("msg", "Invalid value"),
               "type": item.get("type", "validation_error")} for item in exc.errors()]
    if redis:
        await redis.lpush("pharmasafe:quarantine", json.dumps({
            "correlation_id": correlation_id,
            "received_at": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
            "errors": errors,
        }))
        await redis.ltrim("pharmasafe:quarantine", 0, 199)
    return Response(
        content=json.dumps({"detail": errors, "correlation_id": correlation_id}),
        status_code=422,
        media_type="application/json",
        headers={"X-Correlation-ID": correlation_id},
    )

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
    request.state.correlation_id = correlation_id
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

@app.get("/api/v1/dashboard")
async def dashboard():
    """Small live summary for the demo UI; recent cases are backed by Redis."""
    ids = await redis.lrange("pharmasafe:recent_cases", 0, 19)
    recent = []
    counts = {"queued": 0, "processing": 0, "completed": 0, "failed": 0}
    for raw_id in ids:
        case_id = raw_id.decode() if isinstance(raw_id, bytes) else raw_id
        item = await get_case(redis, case_id)
        if not item:
            continue
        counts[item.get("status", "queued")] = counts.get(item.get("status", "queued"), 0) + 1
        recent.append({"case_id": case_id, "status": item.get("status"),
                       "created_at": item.get("created_at"), "result": item.get("result")})
    return {"status": "healthy", "counts": counts, "recent": recent,
            "quarantined_rejections": await redis.llen("pharmasafe:quarantine"),
            "mode": os.getenv("AGENT_MODE", "demo")}

@app.post("/api/v1/cases", status_code=202)
async def submit_case(case: AdverseEventRequest, request: Request):
    # Pydantic validation happens before this function; malformed requests never enter the queue.
    if await redis.exists(f"pharmasafe:case:{case.case_id}"):
        raise HTTPException(status_code=409, detail="case_id already exists; use a new synthetic case ID")
    payload = case.model_dump(mode="json")
    payload["_correlation_id"] = request.state.correlation_id
    await enqueue_case(redis, case.case_id, payload)
    await redis.lpush("pharmasafe:recent_cases", case.case_id)
    await redis.ltrim("pharmasafe:recent_cases", 0, 49)
    RUNS_SUBMITTED.inc()
    logger.info(json.dumps({"event":"case_queued","case_id":case.case_id,
                            "correlation_id":request.state.correlation_id}))
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
