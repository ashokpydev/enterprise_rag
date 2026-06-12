"""
SQLAlchemy Models for Enterprise RAG Platform
Supports multi-tenancy, RBAC, and detailed observability tracking.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
    JSON,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Tenant(Base):
    """
    Multi-tenant tenant record.
    Isolates all data and operations by tenant_id.
    """

    __tablename__ = "tenants"

    tenant_id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    metadata_ = Column(JSON, default={})

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tenant", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """
    Tenant users with RBAC roles.
    Enables role-based security filtering during retrieval.
    """

    __tablename__ = "users"
    __table_args__ = (Index("idx_tenant_user", "tenant_id", "user_id"),)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(255), ForeignKey("tenants.tenant_id"), nullable=False)
    user_id = Column(String(255), nullable=False)
    email = Column(String(255))
    role = Column(String(50), default="user")  # user, hr_manager, admin, etc.
    security_level = Column(String(50), default="public")  # public, internal, confidential, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    queries = relationship("Query", back_populates="user")


class Document(Base):
    """
    Uploaded documents with metadata for retrieval filtering.
    Supports multi-tenant data isolation via tenant_id.
    """

    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_tenant_doc", "tenant_id", "document_id"),
        Index("idx_security_level", "security_level"),
    )

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(255), ForeignKey("tenants.tenant_id"), nullable=False)
    document_id = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    file_type = Column(String(50))  # pdf, docx, txt, etc.
    security_level = Column(String(50), default="public")  # Restrict access via RBAC
    created_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(String(255))
    # A/B testing tracking
    ab_variant = Column(String(50), default="variant_a")
    embedding_model = Column(String(255))
    chunk_size = Column(Integer)
    metadata_ = Column(JSON, default={})

    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """
    Chunks of documents with vector embeddings.
    Enables efficient retrieval via vector similarity search.
    """

    __tablename__ = "document_chunks"
    __table_args__ = (Index("idx_doc_chunk", "document_id"),)

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer)
    text = Column(Text, nullable=False)
    start_char = Column(Integer)
    end_char = Column(Integer)
    # Vector metadata (stored in FAISS, referenced here)
    vector_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")


class Query(Base):
    """
    Query execution log with full trace information.
    Enables cost tracking, performance analysis, and quality evaluation.
    """

    __tablename__ = "queries"
    __table_args__ = (
        Index("idx_tenant_query", "tenant_id", "query_id"),
        Index("idx_query_timestamp", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(255), ForeignKey("tenants.tenant_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    query_id = Column(String(255), nullable=False)
    query_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # A/B Testing
    ab_variant = Column(String(50), default="variant_a")
    embedding_model = Column(String(255))

    # Retrieval Metrics
    documents_retrieved = Column(Integer, default=0)
    retrieval_latency_ms = Column(Float)
    retrieval_scores = Column(JSON)  # List of relevance scores

    # Re-ranking Metrics
    documents_reranked = Column(Integer, default=0)
    reranking_latency_ms = Column(Float)

    # LLM Completion
    llm_model = Column(String(255))
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)
    llm_latency_ms = Column(Float)
    cost_usd = Column(Float)

    # Quality Metrics (populated by LLM-as-Judge)
    is_hallucination = Column(Boolean, default=False)
    hallucination_score = Column(Float)
    context_precision = Column(Float)
    context_recall = Column(Float)
    context_relevance = Column(Float)
    faithfulness_score = Column(Float)

    # Response & Context
    response_text = Column(Text)
    context_used = Column(JSON)  # Retrieved chunks used in prompt

    # Trace & Observability
    trace_id = Column(String(255))  # OpenTelemetry trace ID
    span_ids = Column(JSON)  # List of span IDs

    # Relationships
    tenant = relationship("Tenant", back_populates="queries")
    user = relationship("User", back_populates="queries")


class EvaluationResult(Base):
    """
    LLM-as-Judge evaluation results.
    Asynchronously populated for sampled queries.
    """

    __tablename__ = "evaluation_results"
    __table_args__ = (Index("idx_query_evaluation", "query_id"),)

    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=False)
    evaluation_type = Column(String(50))  # hallucination, context_quality, etc.
    judge_model = Column(String(255))
    score = Column(Float)
    details = Column(JSON)  # Detailed evaluation output
    created_at = Column(DateTime, default=datetime.utcnow)


class ExperimentConfig(Base):
    """
    A/B testing experiment configurations.
    Enables dynamic system parameter variation for testing.
    """

    __tablename__ = "experiment_configs"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(255), ForeignKey("tenants.tenant_id"), nullable=False)
    experiment_name = Column(String(255), nullable=False)
    variant = Column(String(50), nullable=False)  # variant_a, variant_b, etc.
    chunk_size = Column(Integer)
    embedding_model = Column(String(255))
    reranker_model = Column(String(255))
    parameters = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class TokenCostTracking(Base):
    """
    Real-time token cost tracking per tenant.
    Supports multi-tenant billing and cost optimization.
    """

    __tablename__ = "token_cost_tracking"
    __table_args__ = (
        Index("idx_tenant_cost", "tenant_id", "date"),
        Index("idx_cost_date", "date"),
    )

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(255), ForeignKey("tenants.tenant_id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    model = Column(String(255))
    input_tokens_sum = Column(Integer, default=0)
    output_tokens_sum = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    query_count = Column(Integer, default=0)


class AnomalyAlert(Base):
    """
    Tracks system anomalies detected via metrics monitoring.
    Enables proactive issue detection.
    """

    __tablename__ = "anomaly_alerts"
    __table_args__ = (Index("idx_tenant_alert", "tenant_id", "created_at"),)

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String(255), ForeignKey("tenants.tenant_id"), nullable=False)
    alert_type = Column(String(100))  # latency_spike, hallucination_rate_increase, cost_spike
    severity = Column(String(50), default="medium")  # low, medium, high, critical
    message = Column(Text)
    metric_value = Column(Float)
    threshold = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    related_query_ids = Column(JSON)  # References to affected queries
