# PharmaSafe AI — Deployment and Troubleshooting Runbook

## Prerequisites
- Windows and PowerShell
- Docker Desktop running with Linux containers
- Docker Compose v2
- Git

## Start the application

From the repository root:

```powershell
docker compose up -d --build
docker compose ps
```

Check API health:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

## Service URLs

- Frontend: http://localhost:5173
- FastAPI Swagger: http://localhost:8000/docs
- API health: http://localhost:8000/health
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

## View logs

```powershell
docker compose logs --tail=100
docker compose logs --tail=100 api
docker compose logs --tail=100 agent-worker
```

## Stop and rebuild

```powershell
docker compose down
docker compose up -d --build
```

To remove persisted local Redis and Grafana data as well:

```powershell
docker compose down -v
```

Warning: the command above deletes the named Docker volumes.

## Observed development issues and resolutions

These are development troubleshooting observations, not production incidents.

### Docker daemon unavailable
- Symptom: Docker commands could not connect to the Docker engine.
- Cause: Docker Desktop had not finished starting.
- Resolution: Start Docker Desktop, wait for the engine, then verify with `docker info`.

### Redis hostname not resolved when running the API directly on Windows
- Symptom: The API could not resolve the hostname `redis`.
- Cause: `redis` is a Docker Compose service name and resolves within the Compose network.
- Resolution: Run the API and Redis together through Docker Compose.

### Locust requests returned HTTP 422
- Symptom: Initial load-test submissions failed validation.
- Cause: The test payload contained values outside the allowed request schema.
- Resolution: Correct the payload values to match `backend/app/schemas.py` and rerun the test.

## Current limitations
- The agent adapter remains a placeholder pending integration of Member 2's verified LangGraph workflow.
- Redis stores queue and case state; persistent database storage is still future work.
- Durable quarantine storage for rejected submissions is still future work.
- Authentication, comprehensive rate limiting, distributed tracing and complete Grafana dashboards need further implementation.
- Use synthetic data only. Qualified professionals must make final pharmacovigilance decisions.
