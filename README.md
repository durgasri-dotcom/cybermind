# CyberMind - AI-Powered Threat Intelligence Platform

[![Live Demo](https://img.shields.io/badge/Live%20Demo-cybermindai.streamlit.app-00d4ff?style=flat-square&logo=streamlit)](https://cybermindai.streamlit.app)
[![Backend](https://img.shields.io/badge/Backend-cybermind--0y0t.onrender.com-00d4ff?style=flat-square&logo=render)](https://cybermind-0y0t.onrender.com/docs)
[![CI](https://img.shields.io/github/actions/workflow/status/durgasri-dotcom/cybermind/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/durgasri-dotcom/cybermind/actions)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-90%20passed-00ff88?style=flat-square)](https://github.com/durgasri-dotcom/cybermind/actions)

CyberMind is a production-grade AI threat intelligence platform that combines RAG (Retrieval-Augmented Generation), FAISS vector search, LLM-powered analysis, live CVE ingestion from NVD, and full API observability to help security teams understand, triage, and respond to cyber threats in real time.

Built on 691 real MITRE ATT&CK techniques indexed into a FAISS vector store, CyberMind answers natural language security queries, ingests live CVEs from the NVD API with automatic MITRE technique mapping, generates structured incident response playbooks, and persists all data to a production PostgreSQL database with Alembic schema migrations - all powered by LLaMA 3.3 70B via Groq.

---

## Live Demo

| Service     | URL                                                                     |
| ----------- | ----------------------------------------------------------------------- |
| Dashboard   | [cybermindai.streamlit.app](https://cybermindai.streamlit.app)          |
| Backend API | [cybermind-0y0t.onrender.com](https://cybermind-0y0t.onrender.com/docs) |
| API Docs    | [/docs](https://cybermind-0y0t.onrender.com/docs)                       |

---

## Architecture

```mermaid
flowchart TD
    A[MITRE ATT&CK JSON + NVD CVE Feed] --> B[Bronze Layer - Raw Ingestion]
    B --> C[Silver Layer - Normalization + Dedup]
    C --> D[Gold Layer - Risk Scoring + Enrichment]
    D --> E[FAISS Vector Store - 2374 Chunks - all-MiniLM-L6-v2]
    E --> F[RAG Pipeline - LangChain + Semantic Retrieval]
    F --> G[LLM Analysis - Groq - LLaMA 3.3 70B]
    G --> H[FastAPI Backend - SQLAlchemy - Alembic - API Key Auth]
    H --> I[PostgreSQL Database - Render Managed - 6 Tables - Persistent]
    H --> J[Streamlit Dashboard - 7 Tabs - Dark/Light Theme]
```

---

## Tech Stack

| Layer          | Technology                                            |
| -------------- | ----------------------------------------------------- |
| LLM            | Groq API - LLaMA 3.3 70B Versatile                    |
| RAG            | LangChain - FAISS - HuggingFace all-MiniLM-L6-v2      |
| Backend        | FastAPI - Pydantic v2 - Uvicorn                       |
| Database       | PostgreSQL 16 - SQLAlchemy ORM - Alembic Migrations   |
| Auth           | X-API-Key middleware on all write endpoints           |
| CVE Intel      | NVD REST API - CVSS scoring - MITRE ATT&CK mapping    |
| Observability  | Request logging middleware - API analytics endpoint   |
| Dashboard      | Streamlit - Plotly - 7-tab dark/light UI              |
| Data           | MITRE ATT&CK (691 techniques) - NVD CVE (live feed)   |
| Infrastructure | Docker - GitHub Actions CI/CD - Render (Backend + DB) |
| Testing        | pytest - 90 tests                                     |

---

## Features

**RAG-Powered Threat Intelligence Q&A**
Ask anything about MITRE ATT&CK techniques, threat actors, or CVEs in natural language. CyberMind embeds your query, retrieves the top-K semantically similar chunks from the FAISS index, and generates a structured analyst-grade response using LLaMA 3.3.

**Live CVE Ingestion from NVD**
Fetch real CVEs from the NVD API by recency, severity, or keyword. Each CVE is automatically scored with CVSS, CWE weaknesses are extracted, and techniques are mapped to MITRE ATT&CK using heuristic CWE-to-TTP analysis. All data persisted to PostgreSQL with upsert logic.

**Production PostgreSQL Backend with Alembic Migrations**
All alerts, playbooks, entities, CVEs, and request logs are persisted to a managed PostgreSQL 16 database on Render via SQLAlchemy ORM. Schema versioned with Alembic - fully reproducible with `alembic upgrade head`. Data survives every restart, redeploy, and crash - no ephemeral storage.

**AI-Generated Incident Response Playbooks**
Submit any MITRE technique ID and CyberMind generates a structured incident response playbook with containment, eradication, and recovery steps including responsible teams, tools, and time estimates.

**AI-Assisted Alert Triage**
Create security alerts and trigger AI triage - priority recommendation (P1-P4), reasoning, immediate actions, and escalation decision generated by LLaMA 3.3.

**API Key Authentication**
All write endpoints (POST, PATCH, DELETE) protected with X-API-Key header. Read endpoints remain public. Key configured via .env.

**API Observability and Analytics**
Every API request is automatically logged to PostgreSQL - endpoint, method, status code, latency, client IP, timestamp. Query aggregated stats via /api/v1/analytics/requests - total requests, avg latency, top endpoints, slowest endpoints.

**Entity Graph and Threat Actor Profiles**
Add threat actors, malware families, and tools. Visualize entity relationships on an interactive graph. Enrich any entity with an AI-generated threat profile covering TTPs, targeting patterns, and detection recommendations.

**Medallion Data Pipeline**
Bronze to Silver to Gold architecture ingests raw MITRE ATT&CK JSON and NVD CVE feeds, normalizes and scores threats, and produces embedding-ready documents for the vector store.

---

## Project Structure

```
cybermind/
├── configs/                  # Pydantic BaseSettings, structured logging
├── src/
│   ├── backend/
│   │   ├── database/         # SQLAlchemy engine, ORM models, Alembic migrations
│   │   ├── middleware/       # API key auth, request logging
│   │   ├── models/           # Pydantic schemas (threat, alert, playbook, entity, CVE)
│   │   ├── routers/          # FastAPI routers (threats, intel, alerts, playbooks,
│   │   │                     #   entities, cves, analytics, health)
│   │   ├── services/         # RAG, LLM, embeddings, threat scoring, MITRE loader,
│   │   │                     #   CVE service (NVD API)
│   │   └── main.py           # FastAPI app with lifespan, middleware, CORS
│   ├── pipeline/             # MITRE ingest, CVE ingest, transform, vector store build
│   └── dashboard/            # Streamlit 7-tab dashboard
├── data/
│   ├── bronze/               # Raw MITRE ATT&CK JSON
│   ├── silver/               # Normalized threat records
│   └── gold/                 # Scored, embedded, FAISS index
├── tests/                    # 90 tests across pipeline, RAG, playbooks, scoring,
│                             #   database ORM, CVE service, analytics
├── streamlit_app.py          # Standalone Streamlit Cloud entry point
└── .github/workflows/        # CI/CD + scheduled data pipeline
```

---

## Database Schema

| Table           | Description                                                    |
| --------------- | -------------------------------------------------------------- |
| alerts          | Security alerts with priority, status, MITRE technique linkage |
| playbooks       | AI-generated IR playbooks with step-by-step JSON               |
| entities        | Threat actors, malware, tools with relationship graph          |
| cves            | Live CVEs from NVD with CVSS scores and MITRE mappings         |
| request_logs    | Every API call logged with latency and status code             |
| alembic_version | Schema migration version tracking                              |

---

## Quick Start

**1. Clone and install:**

```bash
git clone https://github.com/durgasri-dotcom/cybermind.git
cd cybermind
pip install -r requirements.txt
```

**2. Set up environment:**

```bash
cp .env.example .env
# Add your GROQ_API_KEY, CYBERMIND_API_KEY, and DATABASE_URL to .env
```

For local development, DATABASE_URL defaults to SQLite:

```bash
DATABASE_URL=sqlite:///./cybermind.db
```

For production PostgreSQL:

```bash
DATABASE_URL=postgresql://user:password@host/dbname
```

**3. Run the data pipeline:**

```bash
python -m src.pipeline.ingest_mitre
python -m src.pipeline.transform_threats
python -m src.pipeline.build_vector_store
```

**4. Initialize the database:**

```bash
alembic upgrade head
```

**5. Start the backend:**

```bash
uvicorn src.backend.main:app --reload
```

**6. Start the dashboard:**

```bash
streamlit run src/dashboard/app.py
```

**Or run with Docker:**

```bash
docker-compose up --build
```

---

## API Reference

| Method | Endpoint                          | Auth | Description                               |
| ------ | --------------------------------- | ---- | ----------------------------------------- |
| POST   | /api/v1/intel/query               | -    | RAG-powered threat intelligence Q&A       |
| POST   | /api/v1/intel/similar             | -    | Semantic similarity search                |
| GET    | /api/v1/threats                   | -    | List and filter threat records            |
| POST   | /api/v1/alerts                    | Yes  | Create security alert                     |
| POST   | /api/v1/alerts/{id}/triage        | -    | AI-assisted alert triage                  |
| GET    | /api/v1/alerts                    | -    | List alerts (filterable by status)        |
| POST   | /api/v1/playbooks/generate        | Yes  | Generate AI incident response playbook    |
| GET    | /api/v1/playbooks                 | -    | List saved playbooks                      |
| POST   | /api/v1/entities                  | Yes  | Create threat entity                      |
| POST   | /api/v1/entities/enrich           | -    | LLM entity threat profile                 |
| POST   | /api/v1/cves/ingest/recent        | Yes  | Ingest recent CVEs from NVD               |
| POST   | /api/v1/cves/ingest/severity      | Yes  | Ingest CVEs by severity                   |
| POST   | /api/v1/cves/ingest/keyword       | Yes  | Ingest CVEs by keyword                    |
| GET    | /api/v1/cves                      | -    | List CVEs (filterable by severity)        |
| GET    | /api/v1/cves/stats                | -    | CVE severity distribution and avg CVSS    |
| GET    | /api/v1/analytics/requests        | -    | API usage stats and latency analytics     |
| GET    | /api/v1/analytics/requests/recent | -    | Recent request log feed                   |
| GET    | /api/v1/health                    | -    | Platform health and DB connectivity check |

Auth (Yes) requires X-API-Key header. Full interactive docs at /docs.

---

## Tests

```bash
pytest tests/ -v
# 90 passed
```

Covers threat scoring, RAG retrieval, playbook parsing, MITRE data pipeline, SQLAlchemy ORM (alerts, playbooks, entities, CVEs), CVE service scoring and MITRE mapping, and request log analytics queries.

---

## Deployment

**Streamlit Cloud (Dashboard):**
Deployed at [cybermindai.streamlit.app](https://cybermindai.streamlit.app).

**Render (Backend + PostgreSQL):**

- FastAPI backend deployed at [cybermind-0y0t.onrender.com](https://cybermind-0y0t.onrender.com)
- PostgreSQL 16 managed database on Render (Oregon region)
- Environment variables: DATABASE_URL, GROQ_API_KEY, CYBERMIND_API_KEY

**Docker (Full Stack):**

```bash
docker-compose up --build
# Backend:   http://localhost:8000
# Dashboard: http://localhost:8501
```

---

## Data Sources

- [MITRE ATT&CK Enterprise](https://attack.mitre.org/) - 691 techniques and sub-techniques
- [NVD CVE Feed](https://nvd.nist.gov/developers/vulnerabilities) - live CVE ingestion via REST API

---

Built by Sri Durga Abhigna Tanguturi
