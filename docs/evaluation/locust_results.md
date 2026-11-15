# PharmaSafe AI — Locust Load Test Results

## Test configuration
- Tool: Locust
- Target: Local PharmaSafe AI API
- Concurrent users: 10
- Spawn rate: 2 users per second
- Endpoints: POST /api/v1/cases and GET /health

## Final stopped results

| Metric | POST /api/v1/cases | GET /health |
|---|---:|---:|
| Requests | 184 | 42 |
| Failures | 0 | 0 |
| Median latency | 51 ms | 7 ms |
| p95 latency | 56 ms | 10 ms |
| p99 latency | 150 ms | 10 ms |
| Average latency | 54.04 ms | 7.24 ms |
| Maximum latency | 655 ms | 10 ms |

## Aggregate results

| Metric | Result |
|---|---:|
| Total requests | 226 |
| Total failures | 0 |
| Failure rate | 0% |
| Aggregate p95 latency | 55 ms |
| Concurrent users | 10 |
| Throughput at final snapshot | 4.8 requests/second |

## Interpretation

The final stopped Locust report recorded 226 requests with zero
failures. The case submission endpoint recorded a p95 latency
of 56 ms under the observed 10-user load.

These are local development-environment results, not production
capacity guarantees. Throughput is the rate shown in the final
Locust snapshot.

## Reproduction

Start the application:

```powershell
docker compose up -d --build
```

Start Locust:

```powershell
locust -f .\tests\load\locustfile.py --host http://localhost:8000
```

Open http://localhost:8089 and configure 10 users with a
spawn rate of 2 users per second.

Use synthetic test data only.
