# PharmaSafe AI

**Pharmacovigilance Adverse Event Intake and Triage System**

PharmaSafe AI is a prototype decision-support system for collecting adverse-event reports, validating submissions, processing cases asynchronously, and presenting case status through a web interface.

It uses FastAPI, Redis, a background worker, and a monitoring stack. The agent integration is designed to connect with the verified LangGraph workflow developed by Member 2.

> **Safety notice:** This is an academic prototype. Use synthetic data only. It is not a medical device, a substitute for professional pharmacovigilance assessment, or a regulatory submission system. Final decisions must be made by qualified professionals.

## Architecture

```text
                    Web Client
                 (localhost:5173)
                         |
                         v
                   FastAPI API
                 (localhost:8000)
                         |
                         v
                    Redis Queue
                         |
                         v
                   Agent Worker
                         |
                         v
                Agent Adapter / Graph
                  (Member 2 integration)

Monitoring:
  Prometheus -> API metrics and worker metrics
  Grafana    -> Monitoring interface
```

## Technology Stack

- **Backend:** Python, FastAPI, Pydantic
- **Asynchronous processing:** Redis and background worker
- **Frontend:** HTML, CSS and JavaScript
- **Containerization:** Docker and Docker Compose
- **Monitoring:** Prometheus, Grafana and Prometheus client
- **Load testing:** Locust
- **Testing:** Pytest

## Project Structure

```text
PharmaSafe_AI/
├── backend/
│   ├── app/
│   │   ├── agent_adapter.py
│   │   ├── main.py
│   │   ├── metrics.py
│   │   ├── queue.py
│   │   └── schemas.py
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── worker.py
├── frontend/
│   ├── index.html
│   ├── Dockerfile
│   └── nginx.conf
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
├── tests/
│   └── load/
│       └── locustfile.py
├── docs/
│   ├── evaluation/
│   └── planning/
├── docker-compose.yml
├── pytest.ini
├── .env.example
└── README.md
```

## Prerequisites

- Git
- Docker Desktop
- Docker Compose v2

## Run the application

Clone the repository:

```powershell
git clone https://github.com/sowmyashree3924/PharmaSafe_AI.git
cd PharmaSafe_AI
```

Start all services:

```powershell
docker compose up -d --build
```

Check service status:

```powershell
docker compose ps
```

### Application URLs

| Component | URL |
|---|---|
| Web frontend | http://localhost:5173 |
| FastAPI Swagger UI | http://localhost:8000/docs |
| API health check | http://localhost:8000/health |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

Stop services:

```powershell
docker compose down
```

Remove containers and persistent Redis/Grafana volumes:

```powershell
docker compose down -v
```

**Note:** `docker compose down -v` deletes persisted local application data.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API information |
| GET | `/health` | API and Redis health |
| POST | `/api/v1/cases` | Submit an adverse-event case |
| GET | `/api/v1/cases/{case_id}` | Retrieve case status and result |
| POST | `/api/v1/cases/{case_id}/feedback` | Submit feedback |
| GET | `/metrics` | Prometheus metrics |

### Submit a case

Example request:

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

Submit using the Swagger UI at `/docs` or an HTTP client.

A successful submission returns HTTP `202 Accepted`, with a case ID, queued status and status URL.

Poll the status endpoint:

```text
GET /api/v1/cases/DEMO-001
```

### Feedback

```json
{
  "satisfactory": true,
  "reason": "Example feedback"
}
```

Send this to:

```text
POST /api/v1/cases/DEMO-001/feedback
```

## Testing

Run backend tests from the repository root:

```powershell
python -m pytest -q
```

The pytest configuration uses `backend` as the Python import path.

Run the Locust load test:

```powershell
locust -f .\tests\load\locustfile.py --host http://localhost:8000
```

Open the Locust web interface at:

```text
http://localhost:8089
```

Use synthetic test cases only.

## Monitoring

Prometheus is configured to scrape:

- FastAPI metrics at `api:8000/metrics`
- Background worker metrics at `agent-worker:8001/metrics`

Grafana is provisioned with a Prometheus datasource. Dashboards and additional monitoring panels may be configured through the Grafana interface.

## Current Implementation Status

### Implemented

- FastAPI application and REST endpoints
- Pydantic request and feedback schemas
- Redis-backed asynchronous case queue
- Background worker and agent adapter interface
- Docker Compose deployment with six services
- Frontend intake interface
- Prometheus API and worker metrics endpoints
- Pytest backend tests
- Locust load-test script

### Integration and further work

- Connect and validate Member 2's actual LangGraph workflow.
- Add durable quarantine storage for rejected submissions.
- Add persistent database storage for cases and feedback.
- Complete authentication and rate limiting.
- Add distributed tracing and comprehensive Grafana dashboards.
- Implement and test retry, circuit-breaker and recovery policies.
- Complete end-to-end integration tests and evidence documentation.

The agent adapter currently uses a human-review escalation placeholder until the verified agent workflow is integrated. Do not interpret placeholder output as a clinical assessment.

## Team Contributions

This repository combines work across the project team.

**Member 3 — Backend, frontend and deployment**
- FastAPI backend and API endpoints
- Redis queue and asynchronous worker
- Frontend integration
- Docker Compose configuration
- Prometheus and Grafana integration
- Testing and documentation

Refer to the project planning and handover documents under `docs/planning/` for corpus and evidence details.

## License and Reference Materials

Reference documents are maintained for project research. Check redistribution permissions before sharing source PDFs or extracted full-text copies.
