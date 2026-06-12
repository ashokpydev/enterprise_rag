"""
Dashboard API Routes
Provides metrics and observability data for the dashboard.
"""

from fastapi import APIRouter, Header, Query as FastAPIQuery
from typing import Optional

router = APIRouter()


# ==================== Dashboard Metrics ====================
@router.get("/overview")
async def dashboard_overview(
    x_tenant_id: str = Header(...),
    days: int = FastAPIQuery(default=7),
):
    """Get dashboard overview metrics."""
    return {
        "tenant_id": x_tenant_id,
        "period_days": days,
        "kpis": {
            "total_queries": 1542,
            "avg_latency_ms": 3421,
            "total_cost_usd": 48.32,
            "hallucination_rate": 0.08,
            "avg_context_precision": 0.91,
            "avg_context_recall": 0.92,
        },
        "top_documents": [
            {"id": "doc_1", "queries": 342, "avg_precision": 0.95},
            {"id": "doc_2", "queries": 281, "avg_precision": 0.88},
        ],
    }


@router.get("/traces")
async def get_traces(
    x_tenant_id: str = Header(...),
    limit: int = FastAPIQuery(default=50),
):
    """Get recent query traces for debugging."""
    return {
        "tenant_id": x_tenant_id,
        "traces": [
            {
                "query_id": "query_123",
                "query_text": "What is the salary range for senior engineers?",
                "response_length": 234,
                "latency_ms": 3421,
                "cost_usd": 0.032,
                "hallucination_detected": False,
                "timestamp": "2024-01-15T15:30:00",
            }
        ],
    }


@router.get("/cost-tracking")
async def cost_tracking(
    x_tenant_id: str = Header(...),
    days: int = FastAPIQuery(default=30),
):
    """Get cost breakdown by model and time period."""
    return {
        "tenant_id": x_tenant_id,
        "period_days": days,
        "total_cost_usd": 148.52,
        "by_model": {
            "gpt-4-turbo-preview": {
                "cost_usd": 98.32,
                "input_tokens": 2_340_000,
                "output_tokens": 780_000,
                "query_count": 1542,
            },
            "cross-encoder": {
                "cost_usd": 50.20,
                "queries_reranked": 1542,
            },
        },
        "daily_breakdown": [
            {"date": "2024-01-14", "cost_usd": 8.32},
            {"date": "2024-01-13", "cost_usd": 7.89},
        ],
    }


@router.get("/anomalies")
async def detect_anomalies(
    x_tenant_id: str = Header(...),
):
    """Get detected system anomalies."""
    return {
        "tenant_id": x_tenant_id,
        "anomalies": [
            {
                "type": "latency_spike",
                "severity": "medium",
                "message": "Retrieval latency increased 40% at 14:30 UTC",
                "affected_queries": 23,
                "threshold": 3500,
                "current_value": 4850,
                "timestamp": "2024-01-15T14:30:00",
            }
        ],
    }


@router.get("/a-b-test-results")
async def ab_test_results(
    x_tenant_id: str = Header(...),
    experiment_id: Optional[str] = None,
):
    """Get A/B testing results."""
    return {
        "tenant_id": x_tenant_id,
        "experiments": [
            {
                "name": "Chunk Size Comparison",
                "variant_a": {
                    "name": "512 tokens + MiniLM",
                    "queries": 750,
                    "avg_latency_ms": 3200,
                    "cost_per_query": 0.028,
                    "hallucination_rate": 0.09,
                    "context_precision": 0.89,
                },
                "variant_b": {
                    "name": "1024 tokens + MPNet",
                    "queries": 792,
                    "avg_latency_ms": 3600,
                    "cost_per_query": 0.035,
                    "hallucination_rate": 0.06,
                    "context_precision": 0.93,
                },
                "winner": "variant_b",
                "confidence": 0.87,
            }
        ],
    }
