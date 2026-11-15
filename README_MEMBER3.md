# PharmaSafe AI — Member 3 starter

This is a starter implementation for Member 3 (FastAPI, frontend, Docker and monitoring).
It deliberately does **not** make clinical/regulatory decisions by itself. Until Member 2's
verified LangGraph workflow is connected, the adapter returns a human-review escalation.

## Requirements
- Docker Desktop with Docker Compose v2
- Git

## Run
```bash
docker compose up --build
```
Open:
- Frontend: http://localhost:5173
- FastAPI Swagger: http://localhost:8000/docs
- API health: http://localhost:8000/health
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

Stop:
```bash
docker compose down
```
Remove local Redis/Grafana data:
```bash
docker compose down -v
```

## Services
- `frontend`: simple HTML/JS intake client
- `api`: FastAPI REST service and metrics endpoint
- `agent-worker`: asynchronous Redis queue consumer
- `redis`: queue and run-state storage
- `prometheus`: scrapes API metrics
- `grafana`: dashboard UI (add panels using Prometheus datasource)

## API contract
`POST /api/v1/cases` accepts JSON:
```json
{
  "case_id": "DEMO-001",
  "drug_name": "DemoDrug",
  "reaction_description": "Skin peeling after starting medicine",
  "patient_age": 45,
  "patient_sex": "female",
  "drug_start_date": "2026-11-01T09:00:00",
  "onset_date": "2026-11-08T09:00:00",
  "outcome": "hospitalisation",
  "reporter_type": "doctor"
}
```
It returns HTTP 202 with `case_id`, `status`, and `status_url`.
Poll `GET /api/v1/cases/{case_id}` until `completed` or `failed`.
Feedback: `POST /api/v1/cases/{case_id}/feedback` with
`{"satisfactory": true, "reason": "..."}`.

Allowed outcome values: `recovered`, `recovering`, `not_recovered`, `fatal`,
`hospitalisation`, `disability`, `congenital_anomaly`, `unknown`.

## Member 2 integration — required before clinical demo
Edit `backend/app/agent_adapter.py`. Replace the placeholder `run_agent()` body with
an import and invocation of Member 2's actual graph. Agree on:
1. function name and async/sync behavior;
2. input schema (the validated case payload);
3. output schema: decision status, seriousness, expectedness, route, citations,
   verification status and escalation reason;
4. timeout/error behavior.

The adapter must return escalation if evidence verification fails, timing is unclear,
the drug is outside the corpus, or the graph fails. Never manufacture citations or
infer regulatory timelines in this API layer.

## Important limitations / remaining work
This starter is an integration scaffold, not a completed rubric submission:
- Add durable quarantine storage for rejected payloads and field-level validation errors.
- Add a persistent database for cases/feedback; current Redis state is ephemeral.
- Add authentication/client rate limiting if required by your team's threat model.
- Add OpenTelemetry tracing, structured per-step logs, Grafana dashboards and container metrics.
- Add API/worker retry policy and provider circuit breaker at the agent/provider adapter.
- Add a genuine incident-log entry after observing a real development failure.
- Add Locust tests with an LLM stub and declare/measure the p95 SLO before testing.
- Configure queue depth accurately and test worker scaling with `docker compose up --scale agent-worker=3`.
- Add tests and ensure all citations resolve to retrieved passages.

## Safety
Use synthetic cases only. This is decision support, not a medical device or regulatory submission.
A qualified pharmacovigilance professional must make the final decision.
