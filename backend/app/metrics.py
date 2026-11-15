from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

REQUESTS = Counter("pharmasafe_api_requests_total", "API requests", ["endpoint", "method", "status"])
RUNS_SUBMITTED = Counter("pharmasafe_runs_submitted_total", "Case runs submitted")
RUNS_COMPLETED = Counter("pharmasafe_runs_completed_total", "Case runs completed")
RUNS_FAILED = Counter("pharmasafe_runs_failed_total", "Case runs failed")
RUN_LATENCY = Histogram("pharmasafe_run_duration_seconds", "End-to-end processing time")
QUEUE_DEPTH = Gauge("pharmasafe_queue_depth", "Pending case count")
