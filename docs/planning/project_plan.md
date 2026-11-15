

\# PharmaSafe AI

\## Project Plan



\### Course

UE24AM342AA5 - ML System Design and AgentOps



\### Project Objective

To develop a multi-agent pharmacovigilance intake and triage service that validates synthetic adverse event reports, retrieves pharmaceutical reference evidence, assesses seriousness and expectedness, and generates an evidence-supported reporting recommendation.



\### Main Components

1\. Report ingestion and validation

2\. Pharmaceutical document processing

3\. Vector database and semantic retrieval

4\. Evidence Research Agent

5\. Assessment and Verification Agent

6\. Reporting recommendation

7\. Human escalation

8\. FastAPI backend

9\. Web frontend

10\. Monitoring and observability



\### Reference Corpus

1\. New Drugs and Clinical Trials Rules, 2019

2\. IPC Pharmacovigilance Guidance, Version 2.0

3\. One guide-approved marketed drug package insert



\### Technology Stack

\- Python

\- FastAPI

\- LangGraph

\- LangChain

\- ChromaDB

\- Sentence Transformers

\- Redis

\- Docker Compose

\- Prometheus

\- Grafana

\- OpenTelemetry

\- Jaeger

\- Locust



\### Safety Scope

\- Synthetic reports only

\- No real patient information

\- No automatic regulatory report submission

\- Human review for uncertain cases

\- Every recommendation must have supporting evidence



\### Team Responsibilities

Member 1: Corpus and retrieval

Member 2: Multi-agent system and evaluation

Member 3: API, frontend and deployment



