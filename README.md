# PharmaSafe AI

**Pharmacovigilance adverse-event intake and triage demo**

PharmaSafe AI accepts synthetic adverse-event reports, validates them at the REST boundary, processes them through a Redis-backed worker, and presents an evidence-linked assessment in a web dashboard. It is an academic decision-support prototype. It does not diagnose, prove causality, submit regulatory reports, or make final medical or regulatory decisions. A qualified pharmacovigilance professional makes the final decision.

## Start the demo

Requirements: Git, Docker Desktop, and Docker Compose v2.

```powershell
git clone https://github.com/sowmyashree3924/PharmaSafe_AI.git
cd PharmaSafe_AI
docker compose up --build
```

No `.env` file, provider credential, model download, or manual index build is needed for the default local demo. The first start builds the containers. Open:

| Service | Address |
|---|---|
| Dashboard | http://localhost:5173 |
| REST API / OpenAPI | http://localhost:8000/docs |
| Health | http://localhost:8000/health |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

Click **Assess case** to submit the prefilled synthetic lamotrigine skin-peeling scenario. Processing is asynchronous: the API returns a queued case, and the dashboard polls until the worker finishes. Use **Load demo case** for another unique ID. Stop the stack with `Ctrl+C`, or run `docker compose down`.

## Demo assessment and limits

The default `AGENT_MODE=demo` uses a bounded, local evidence-first workflow with separate intake, evidence, verification, and routing responsibilities. It needs no LLM and does not send case text to an external provider. The workflow performs a case-field lookup, label/corpus search, clause lookup, then checks that all displayed citations resolve to retrieved passages. Run trace, step latency, prompt/version label, and tool count are included with the result.

The prefilled scenario uses two reference sources:

1. IPC Pharmacovigilance Guidance v2.0 (2024), seriousness criterion in §2.5.3.6 and serious-event reporting provision in §2.7.1, from the project evidence notes.
2. A DailyMed lamotrigine U.S. label excerpt, indexed in [docs/planning/lamotrigine_label_excerpt.md](docs/planning/lamotrigine_label_excerpt.md), which matches “skin peeling” to the serious-skin-reaction warning and provides timing context.

The supplied project corpus did not contain the selected drug insert. The DailyMed source is a U.S. label, not a verified India-approved product insert. The demo therefore marks expectedness as a U.S.-label match, leaves local expectedness confirmation to a qualified reviewer, and shows a provisional expedited-reporting review based on seriousness. It does not assert that lamotrigine caused the event or automatically apply the U.S. label to Indian regulatory assessment. Replace this excerpt with the appropriate approved local product information before representing the expectedness result as final.

Cases for drugs without matching label evidence, missing evidence, or suspicious instruction-like free text escalate for human review. The demo uses synthetic data only. Do not submit real patient information.

## Submit a case using the API

```powershell
$body = @{
  case_id = "DEMO-101"
  drug_name = "Lamotrigine"
  reaction_description = "Skin peeling after starting medicine; admitted to hospital"
  patient_age = 45
  patient_sex = "female"
  drug_start_date = "2026-11-01T09:00:00Z"
  onset_date = "2026-11-08T09:00:00Z"
  outcome = "hospitalisation"
  reporter_type = "doctor"
} | ConvertTo-Json

$submission = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/cases `
  -ContentType "application/json" -Body $body
Invoke-RestMethod ("http://localhost:8000" + $submission.status_url)
```

The published Pydantic contract enforces required fields, date ordering, age range, categories, and field lengths before queueing. Rejected input returns HTTP 422 with field-level errors and is quarantined as metadata only; submitted free-text values are not stored in the quarantine record. A repeated case ID returns HTTP 409.

## Interfaces

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | API and Redis health |
| `GET` | `/api/v1/dashboard` | Recent run counts, case list, quarantine count, operating mode |
| `POST` | `/api/v1/cases` | Validate and queue an adverse-event report (202) |
| `GET` | `/api/v1/cases/{case_id}` | Poll run status/result |
| `POST` | `/api/v1/cases/{case_id}/feedback` | Persist caller feedback in Redis |
| `GET` | `/metrics` | Prometheus API metrics |
| `GET` | `:8001/metrics` | Worker metrics inside the Compose network |

The result includes seriousness, expectedness, recommendation, human-review reasons, citations with source and section/page, verification status, and an agent-step trace. The API never transmits a regulatory report.

## Services and design

```text
Browser dashboard ──> FastAPI intake ──> Redis queue ──> Agent worker
                            │                                  │
                            └── Prometheus <── worker metrics ─┘
                                  │
                                Grafana
```

The API validates quickly and returns a run ID; Redis separates request latency and API failure from slower worker execution. The worker can be scaled independently, for example `docker compose up --build --scale agent-worker=3`. The dashboard polls the status endpoint because the demonstration is local and does not need callback infrastructure.

The worker exposes completed/failed run counts, queue depth, and end-to-end worker latency. Prometheus scrapes API and worker metrics. Grafana is provisioned with a Prometheus data source; extend its dashboard panels for a full operational SLO view.

## Configuration

`.env.example` documents optional settings. Copy it to `.env` only when changing defaults. The default path starts in local deterministic demo mode. The LangGraph/provider path remains a separate integration scaffold; it also needs extracted corpus files and a built FAISS index before it can run. Its settings are `AGENT_MODE=langgraph`, `INSTALL_AGENT_DEPS=true`, a locally configured provider credential, and the provider model setting. Never commit `.env` or credentials. The local demo does not need them.

## Repository map

```text
backend/app/                 FastAPI API, schemas, Redis queue
backend/agents/demo_agent.py Local evidence-first demonstration workflow
backend/agents/              Optional LangGraph workflow and retrieval tools
frontend/index.html          Intake and live operations dashboard
docs/planning/               Corpus notes, evidence index and label excerpt
monitoring/                  Prometheus and Grafana provisioning
docker-compose.yml           Local multi-service deployment
```

## Project scope

The current demo prioritizes a working end-to-end intake, bounded worker run, cited evidence display, conservative escalation, and repeatable local startup. It is not a validated production pharmacovigilance system. The approved local label, broader expectedness mapping, durable case database, authentication, provider circuit breaker, distributed tracing, full evaluation/load report, and complete Grafana dashboard remain follow-up work. The academic brief and corpus handover are maintained under `docs/planning/`.
