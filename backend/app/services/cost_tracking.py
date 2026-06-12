"""
Cost Tracking Service
Real-time token usage and cost tracking per tenant.
Enables multi-tenant billing and cost optimization.
"""

from typing import Dict, Any
from datetime import datetime, timedelta
from app.core.config import settings


class CostTrackingService:
    """
    Tracks token costs in real-time for multi-tenant billing.
    """

    # Pricing tables (can be pulled from database for dynamic pricing)
    PRICING = {
        "gpt-4-turbo-preview": {
            "input": 0.01 / 1000,  # $0.01 per 1K tokens
            "output": 0.03 / 1000,  # $0.03 per 1K tokens
        },
        "gpt-3.5-turbo": {
            "input": 0.0005 / 1000,
            "output": 0.0015 / 1000,
        },
        "cross-encoder": {
            "inference": 0.00001 / 100,  # Cost per 100 inferences
        },
        "embedding": {
            "per_token": 0.00002 / 1000,
        },
    }

    @staticmethod
    def calculate_llm_cost(
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Calculate cost for LLM inference."""
        if model not in CostTrackingService.PRICING:
            return 0.0

        pricing = CostTrackingService.PRICING[model]
        return input_tokens * pricing["input"] + output_tokens * pricing["output"]

    @staticmethod
    def calculate_embedding_cost(tokens: int) -> float:
        """Calculate cost for embeddings."""
        pricing = CostTrackingService.PRICING["embedding"]
        return tokens * pricing["per_token"]

    @staticmethod
    def get_tenant_daily_cost(tenant_id: str, date: datetime) -> Dict[str, Any]:
        """Get daily cost summary for tenant."""
        # Would query database
        return {
            "tenant_id": tenant_id,
            "date": date.strftime("%Y-%m-%d"),
            "total_cost": 48.32,
            "by_model": {
                "gpt-4": 32.15,
                "cross-encoder": 12.50,
                "embeddings": 3.67,
            },
            "token_summary": {
                "input_tokens": 2_340_000,
                "output_tokens": 780_000,
            },
        }

    @staticmethod
    def get_tenant_monthly_forecast(tenant_id: str) -> Dict[str, Any]:
        """Forecast monthly costs based on recent usage."""
        # Would query database and calculate trends
        return {
            "tenant_id": tenant_id,
            "current_month_cost": 1452.10,
            "projected_monthly_cost": 1890.50,
            "trend": "increasing",  # increasing, stable, decreasing
            "cost_per_query": 0.94,
        }


class AnomalolyDetectionService:
    """
    Detects system anomalies in metrics.
    Alerts on latency spikes, cost anomalies, quality degradation.
    """

    @staticmethod
    def detect_latency_anomaly(current_latency: float, baseline_latency: float) -> bool:
        """
        Detect if latency has spiked beyond threshold.
        Threshold: >40% increase from baseline.
        """
        percentage_increase = (current_latency - baseline_latency) / baseline_latency * 100
        return percentage_increase > 40

    @staticmethod
    def detect_cost_anomaly(daily_cost: float, avg_daily_cost: float) -> bool:
        """
        Detect if daily cost is anomalously high.
        Threshold: >50% above average.
        """
        percentage_increase = (daily_cost - avg_daily_cost) / avg_daily_cost * 100
        return percentage_increase > 50

    @staticmethod
    def detect_hallucination_rate_anomaly(
        current_rate: float,
        baseline_rate: float,
    ) -> bool:
        """
        Detect if hallucination rate has increased.
        Threshold: >30% absolute increase.
        """
        return (current_rate - baseline_rate) > 0.30

    @staticmethod
    def detect_vector_db_degradation(avg_retrieval_latency: float) -> bool:
        """
        Detect if vector DB performance has degraded.
        Threshold: >500ms retrieval latency.
        """
        return avg_retrieval_latency > 500
