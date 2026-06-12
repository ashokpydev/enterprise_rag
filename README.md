# Enterprise RAG Platform with Observability Dashboard

> **Production-grade RAG system** that separates you from junior developers by focusing on **telemetry, safety, multi-tenancy, and governance** around the LLM.

## 🏗️ Architecture Overview

This platform implements a **3-tier distributed architecture** separating data collection from downstream analysis:

```
┌─────────────────────────────────────────────────────────────────┐
│                       INGESTION & QUERY APIs                    │
│                  (FastAPI + Multi-Tenant Support)               │
│  • /documents/upload  → Async chunking & embedding (Celery)    │
│  • /query            → Hybrid search + LLM completion           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓ OpenTelemetry (OTLP)
┌─────────────────────────────────────────────────────────────────┐
│          OBSERVABILITY LAYER (Signal Collection)                │
│  • Trace spans: Retrieval, Re-ranking, LLM, Evaluation         │
│  • Metrics: Token usage, latency, cost per operation           │
│  • Attributes: OpenInference spec compliance                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓ gRPC/HTTP Export
┌─────────────────────────────────────────────────────────────────┐
│      ANALYTICS & GUARDRAIL LAYER (Signal Analysis)              │
│  • Arize Phoenix / Jaeger: Trace storage & visualization       │
│  • Prometheus: Metrics aggregation                              │
│  • LLM-as-Judge: Async quality evaluation (10% sampling)       │
│  • Anomaly Detection: Cost spikes, hallucination increases      │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ↓ Query & Aggregate
┌─────────────────────────────────────────────────────────────────┐
│      OBSERVABILITY DASHBOARD (React Frontend)                   │
│  • Real-time KPIs: Latency, cost, hallucination rate          │
│  • A/B Test Results: Side-by-side variant comparison           │
│  • Cost Tracking: Per-tenant billing, cost forecasting         │
│  • Anomaly Alerts: Proactive system monitoring                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### 1. Clone & Setup

```bash
git clone <repo>
cd enterprise_rag

# Copy environment template
cp backend/.env.example backend/.env
# Edit backend/.env with your OpenAI API key
```

### 2. Start Services

```bash
# Start all services (API, DB, Redis, Celery, Dashboard)
docker-compose up -d

# Initialize database
docker-compose exec api python -m app.core.database

# Check services
docker-compose ps
```

### 3. Verify Deployment

```bash
# API health
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs

# Dashboard
open http://localhost:3000
```

## 📊 Core Features

### 1. **Multi-Tenant Isolation**
Every operation is tenant-aware and secure:
```bash
curl http://localhost:8000/api/v1/query \
  -H "X-Tenant-ID: enterprise-x" \
  -H "X-User-ID: user-123" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is our Q4 strategy?"}'
```

- Mandatory `X-Tenant-ID` header on all requests
- Database-layer filtering with `tenant_id` column
- Vector store metadata filtering for data isolation
- Role-based access control (RBAC) for sensitive documents

### 2. **OpenTelemetry Instrumentation**
Standardizes telemetry on **OpenInference** specs

### 3. **Hybrid Search + Re-ranking Pipeline**
Vector search + cross-encoder re-ranking for quality

### 4. **LLM-as-Judge Evaluation**
Automatic quality scoring on sampled queries

### 5. **A/B Testing Framework**
Dynamic system parameter variation with dashboard comparison

### 6. **Cost Tracking & Billing**
Real-time token usage and cost attribution per tenant

## 📈 API Endpoints

### Query Execution
```bash
POST /api/v1/query
Headers:
  X-Tenant-ID: <tenant_id>
  X-User-ID: <user_id>
```

### Document Upload
```bash
POST /api/v1/documents/upload
```

### Dashboard Metrics
```bash
GET /api/v1/dashboard/overview
GET /api/v1/dashboard/cost-tracking
GET /api/v1/dashboard/anomalies
```

## 📁 Project Structure

```
enterprise_rag/
├── backend/
│   ├── app/
│   │   ├── core/              # Config, database, settings
│   │   ├── api/               # FastAPI routes
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── services/          # Business logic
│   │   ├── telemetry/         # OpenTelemetry instrumentation
│   │   ├── tasks/             # Celery async tasks
│   │   └── main.py            # FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔒 Multi-Tenancy & RBAC

- Database-layer filtering with `tenant_id`
- Vector store metadata filtering
- Mandatory `X-Tenant-ID` header validation
- Role-based security filtering in retrieval

## 🎯 Production Ready

This platform demonstrates enterprise-grade engineering:
- ✅ Asynchronous processing (Celery)
- ✅ OpenTelemetry standardized instrumentation
- ✅ Multi-tenant data isolation
- ✅ Automated quality evaluation
- ✅ Cost tracking and optimization
- ✅ A/B testing framework
- ✅ Anomaly detection
- ✅ Full observability dashboard

---

**Built to demonstrate senior platform engineering skills** 🚀
