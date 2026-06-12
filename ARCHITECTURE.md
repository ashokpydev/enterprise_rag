# Enterprise RAG Platform - Architecture Document

## System Design Principles

This document outlines the architectural decisions and patterns used in the Enterprise RAG Platform.

### 1. **Three-Tier Architecture**

The platform separates concerns across three distinct tiers:

```
Data Collection (APIs) → Signal Processing (Telemetry) → Analysis (Dashboard)
```

**Benefits:**
- Each tier can scale independently
- Telemetry collection doesn't impact API latency
- Analysis/dashboards don't require real-time database queries
- Easy to swap backends (OpenAI → Anthropic, Jaeger → Datadog)

### 2. **Multi-Tenant by Default**

Every table has a `tenant_id` column:
- Database-layer isolation prevents accidental data leaks
- Vector store metadata filtering ensures retrieval isolation
- All APIs require `X-Tenant-ID` header
- Query traces are tagged with tenant for multi-tenant billing

**Security Model:**
```
Request → Tenant Validation → DB Filter → Vector Filter → Response
```

### 3. **OpenTelemetry Standardization**

All instrumentation follows **OpenInference specification**:
- Vendor-neutral (can swap Jaeger, Arize, Datadog)
- Standard attribute names enable ecosystem tooling
- Semantic conventions (gen_ai.*, retrieval.*, rag.*)
- Structured traces with parent-child relationships

### 4. **Asynchronous Processing**

Heavy operations don't block API requests:
- Document ingestion: Celery background tasks
- Quality evaluation: Sampled async tasks
- Anomaly detection: Periodic batch jobs
- Email notifications: Fire-and-forget

**Trade-off:** Eventual consistency instead of immediate results

### 5. **Cost-First Design**

Every operation tracks costs:
- Token usage is logged at the span level
- Real-time cost attribution to tenants
- Monthly forecasting for budget planning
- A/B testing comparison includes cost metrics

**Example:** Re-ranking on 100 candidates instead of 1000 saves 90% of cross-encoder inference cost.

### 6. **Quality Evaluation**

LLM-as-Judge approach:
- Cheaper judge model evaluates expensive production queries
- Sampling (10%) for cost efficiency
- Async evaluation for latency isolation
- Scores stored back on query traces

**Metrics Evaluated:**
- Hallucination detection
- Context precision
- Context recall
- Faithfulness

## Data Flow Diagrams

### Query Execution Flow
```
User Request
    ↓
FastAPI Route (/query)
    ├─ Validate tenant_id header
    ├─ Create parent trace span
    ↓
RAG Retrieval Service
    ├─ Vector Search (with tenant filtering)
    │   └─ Create child span with metrics
    ├─ Cross-Encoder Re-ranking
    │   └─ Create child span with scores
    ↓
LLM Completion Service
    ├─ Build prompt with context
    ├─ Call LLM API
    │   └─ Track tokens and cost
    ├─ Create child span with metrics
    ↓
Evaluation (if sampled)
    ├─ Send to Celery task queue
    ├─ Async judge evaluation
    │   └─ Update query record with scores
    ↓
Response to User
    └─ Include trace_id for debugging
```

### Document Ingestion Flow
```
File Upload (/documents/upload)
    ↓
FastAPI Route
    ├─ Validate tenant_id
    ├─ Store file metadata in DB
    ├─ Send to Celery task
    ↓
Async Celery Worker
    ├─ Read file content
    ├─ Split into chunks (configurable by A/B variant)
    ├─ Generate embeddings (sentence-transformers)
    ├─ Add to FAISS index
    ├─ Store metadata in DB
    ↓
Response to User (immediate)
    └─ document_id for future reference
```

## Database Schema

### Tenant Isolation Pattern
Every table includes:
```sql
tenant_id VARCHAR(255) NOT NULL,
FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
INDEX idx_tenant_<table_name> (tenant_id, <primary_key>)
```

### Cost Tracking Pattern
Every query logs:
```python
{
    "input_tokens": 2340,
    "output_tokens": 780,
    "model": "gpt-4-turbo-preview",
    "cost_usd": 0.0940,
    "tenant_id": "enterprise-x"
}
```

### Quality Metrics Pattern
Scores stored on Query record:
```python
{
    "is_hallucination": False,
    "hallucination_score": 0.08,
    "context_precision": 0.91,
    "context_recall": 0.92,
    "faithfulness_score": 0.94
}
```

## Deployment Architecture

### Development (Docker Compose)
```
┌──────────────────┐
│  Docker Compose  │
├──────────────────┤
│ • API (FastAPI)  │
│ • Celery Worker  │
│ • PostgreSQL     │
│ • Redis          │
│ • Dashboard      │
└──────────────────┘
```

### Production (Kubernetes)
```
┌──────────────────┬──────────────────┬──────────────────┐
│ API Deployment   │ Worker Deployment│ Scheduler        │
│ (3+ replicas)    │ (5+ replicas)    │ (1 instance)     │
├──────────────────┼──────────────────┼──────────────────┤
│ FastAPI Service  │ Celery Worker    │ Celery Beat      │
│ (Load balanced)  │ (Queue consumer) │ (Periodic tasks) │
└──────────────────┴──────────────────┴──────────────────┘
         ↓                 ↓                    ↓
┌──────────────────────────────────────────────────────────┐
│          PostgreSQL (Managed RDS)                        │
│  • Main DB for metadata, queries, cost tracking         │
└──────────────────────────────────────────────────────────┘
         ↓                 ↓
┌──────────────────┬──────────────────┐
│   Redis Cache    │  FAISS Cluster   │
│  (Elasticache)   │  (Search nodes)  │
└──────────────────┴──────────────────┘
         ↓
┌──────────────────────────────────────────────────────────┐
│  OpenTelemetry Collector                                 │
│  └─→ Traces: Jaeger/Datadog/Arize                       │
│  └─→ Metrics: Prometheus/CloudMonitoring               │
└──────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────┐
│  React Dashboard (CDN)                                   │
│  └─→ Visualizes metrics and traces                      │
└──────────────────────────────────────────────────────────┘
```

## Performance Optimizations

### 1. **Vector Search Optimization**
- FAISS IndexFlatL2 for small-medium datasets (~100K embeddings)
- Metadata filtering in-memory (tenant_id, security_level)
- Top-k * 2 candidate retrieval for re-ranking

### 2. **Re-ranking Efficiency**
- Only re-rank candidate set (100 docs), not entire index
- Lightweight cross-encoder model (12 layers)
- Batch scoring for throughput

### 3. **Token Cost Reduction**
- Smaller context window via re-ranking
- Prompt caching (future optimization)
- Token budget per tenant

### 4. **Caching Strategy**
- Redis cache for embedding lookups (TTL: 1 hour)
- Query result caching for identical queries
- Vector search cache for common queries

## Scaling Considerations

### Horizontal Scaling
- **API**: Load balance behind reverse proxy (NGINX/ALB)
- **Celery**: Increase worker replicas, pool from Redis queue
- **FAISS**: Migrate to Pinecone/Weaviate for larger datasets
- **Database**: Implement sharding by tenant_id

### Vertical Scaling
- Increase Celery worker CPU for embedding generation
- Increase Redis memory for cache
- Increase PostgreSQL instance size

### Observability Scaling
- Trace sampling at 10-50% in production
- Metric aggregation windows (1m, 5m, 1h)
- Retention policies (30-90 days for traces)

## Security Best Practices

1. **API Authentication**
   - API keys per tenant (stored in secrets manager)
   - JWT tokens for dashboard access
   - Rate limiting per tenant

2. **Data Encryption**
   - TLS in transit (HTTPS)
   - Encryption at rest (PostgreSQL)
   - Field-level encryption for sensitive data

3. **Multi-Tenancy Isolation**
   - Query authorization via tenant_id
   - Row-level security policies
   - Audit logging for sensitive operations

## Future Enhancements

1. **Advanced Search**
   - Implement BM25 keyword search
   - Hybrid search scoring (semantic + keyword)
   - Query expansion and reformulation

2. **Advanced Evaluation**
   - Fine-tuned judge models per domain
   - Human feedback loop for calibration
   - Batch evaluation pipelines

3. **Cost Optimization**
   - Prompt compression
   - Token prediction and pre-caching
   - Model auto-switching based on cost/quality

4. **Scalability**
   - FAISS → Pinecone/Weaviate migration
   - Database sharding
   - Distributed training for fine-tuning
