"""
OpenTelemetry Instrumentation & Span Management
Standardizes all telemetry on OpenInference specifications.
"""

from typing import Any, Dict, Optional
from contextlib import contextmanager
import json

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.trace.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.metrics.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

from app.core.config import settings


class TelemetryManager:
    """
    Centralized telemetry management following OpenInference specifications.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize_telemetry()
            TelemetryManager._initialized = True

    def _initialize_telemetry(self):
        """Initialize OpenTelemetry providers and exporters."""
        if not settings.OTEL_ENABLED:
            self.tracer_provider = None
            self.meter_provider = None
            return

        # Create resource with service metadata
        resource = Resource.create(
            {
                ResourceAttributes.SERVICE_NAME: settings.OTEL_SERVICE_NAME,
                ResourceAttributes.SERVICE_VERSION: settings.OTEL_SERVICE_VERSION,
                "environment": settings.ENVIRONMENT,
            }
        )

        # Initialize Trace Provider
        otlp_trace_exporter = OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            headers={"signoz-access-token": ""},  # Add auth if needed
        )

        self.tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(self.tracer_provider)
        self.tracer_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))

        # Initialize Metrics Provider
        otlp_metrics_exporter = OTLPMetricExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        )

        metric_reader = PeriodicExportingMetricReader(otlp_metrics_exporter)
        self.meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(self.meter_provider)

        # Instrument libraries
        self._instrument_libraries()

    def _instrument_libraries(self):
        """Instrument third-party libraries with OpenTelemetry."""
        try:
            FastAPIInstrumentor().instrument()
            SQLAlchemyInstrumentor().instrument()
            CeleryInstrumentor().instrument()
            RequestsInstrumentor().instrument()
        except Exception as e:
            print(f"Warning: Failed to instrument libraries: {e}")

    def get_tracer(self, name: str = __name__) -> trace.Tracer:
        """Get a tracer instance for creating spans."""
        if self.tracer_provider:
            return self.tracer_provider.get_tracer(name)
        return trace.get_tracer(name)

    def get_meter(self, name: str = __name__) -> metrics.Meter:
        """Get a meter instance for recording metrics."""
        if self.meter_provider:
            return self.meter_provider.get_meter(name)
        return metrics.get_meter(name)


# Global instance
telemetry_manager = TelemetryManager()


class RAGSpanAttributes:
    """
    Standard span attributes following OpenInference specification for RAG systems.
    https://github.com/Arize-ai/openinference/tree/main/spec/
    """

    # ==================== Retrieval Span Attributes ====================
    @staticmethod
    def retrieval_span(
        tenant_id: str,
        user_id: str,
        query: str,
        documents_retrieved: int,
        retrieval_latency_ms: float,
        document_ids: Optional[list[str]] = None,
        scores: Optional[list[float]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Attributes for vector database retrieval span.
        Tracks what documents were retrieved and their relevance scores.
        """
        return {
            # Multi-tenancy tracking
            "tenant_id": tenant_id,
            "user_id": user_id,
            # OpenInference standard attributes
            "gen_ai.system": "rag",
            "retrieval.query": query,
            "retrieval.documents_returned": documents_retrieved,
            "retrieval.latency_ms": retrieval_latency_ms,
            # Detailed retrieval metrics
            "retrieval.document_ids": json.dumps(document_ids or []),
            "retrieval.relevance_scores": json.dumps(scores or []),
            "retrieval.metadata_filters": json.dumps(filters or {}),
        }

    # ==================== Re-ranking Span Attributes ====================
    @staticmethod
    def reranking_span(
        original_rank_count: int,
        reranked_count: int,
        reranking_latency_ms: float,
        top_scores: Optional[list[float]] = None,
        model_used: str = "cross-encoder",
    ) -> Dict[str, Any]:
        """
        Attributes for cross-encoder re-ranking span.
        Tracks how re-ranking changed document order and quality.
        """
        return {
            "gen_ai.system": "rag",
            "reranking.original_count": original_rank_count,
            "reranking.final_count": reranked_count,
            "reranking.latency_ms": reranking_latency_ms,
            "reranking.top_scores": json.dumps(top_scores or []),
            "reranking.model": model_used,
        }

    # ==================== LLM Span Attributes ====================
    @staticmethod
    def llm_span(
        model: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        latency_ms: float,
        temperature: float,
        max_tokens: int,
        tenant_id: Optional[str] = None,
        cost_usd: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Attributes for LLM completion span following OpenInference spec.
        Tracks exact token usage for cost attribution.
        """
        return {
            # OpenInference LLM attributes
            "gen_ai.system": "openai",
            "gen_ai.request.model": model,
            "gen_ai.request.temperature": temperature,
            "gen_ai.request.max_tokens": max_tokens,
            "gen_ai.usage.input_tokens": input_tokens,
            "gen_ai.usage.output_tokens": output_tokens,
            "gen_ai.usage.total_tokens": total_tokens,
            "gen_ai.latency_ms": latency_ms,
            # Cost tracking (multi-tenant billing)
            "cost_usd": cost_usd,
            "tenant_id": tenant_id,
        }

    # ==================== Hallucination Detection Span ====================
    @staticmethod
    def hallucination_check_span(
        is_hallucination: bool,
        hallucination_score: float,
        grounded_claims: int,
        ungrounded_claims: int,
        evaluation_model: str = "gpt-4-turbo-preview",
    ) -> Dict[str, Any]:
        """
        Attributes for LLM-as-Judge hallucination evaluation span.
        Detects if response is grounded in retrieved context.
        """
        return {
            "gen_ai.system": "rag",
            "evaluation.type": "hallucination_detection",
            "evaluation.is_hallucination": is_hallucination,
            "evaluation.hallucination_score": hallucination_score,
            "evaluation.grounded_claims": grounded_claims,
            "evaluation.ungrounded_claims": ungrounded_claims,
            "evaluation.model": evaluation_model,
        }

    # ==================== Context Quality Span ====================
    @staticmethod
    def context_quality_span(
        context_precision: float,
        context_recall: float,
        context_relevance: float,
        num_relevant_docs: int,
        num_total_docs: int,
    ) -> Dict[str, Any]:
        """
        Attributes for context quality evaluation span (RAG Triad).
        Measures retrieval effectiveness.
        """
        return {
            "gen_ai.system": "rag",
            "evaluation.type": "context_quality",
            "rag.context_precision": context_precision,
            "rag.context_recall": context_recall,
            "rag.context_relevance": context_relevance,
            "rag.relevant_documents": num_relevant_docs,
            "rag.total_documents": num_total_docs,
        }


@contextmanager
def record_rag_span(
    span_name: str,
    attributes: Optional[Dict[str, Any]] = None,
):
    """
    Context manager for recording RAG operation spans.

    Usage:
        with record_rag_span("retrieval", attributes):
            # Your code here
            pass
    """
    tracer = telemetry_manager.get_tracer(__name__)
    with tracer.start_as_current_span(span_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span


def shutdown_telemetry():
    """Gracefully shutdown telemetry providers."""
    if telemetry_manager.tracer_provider:
        telemetry_manager.tracer_provider.force_flush(timeout_millis=30000)
    if telemetry_manager.meter_provider:
        telemetry_manager.meter_provider.force_flush(timeout_millis=30000)
