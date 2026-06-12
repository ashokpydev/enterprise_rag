"""
Integration Tests for Enterprise RAG Platform
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_tenant():
    return {
        "tenant_id": "test-tenant-123",
        "user_id": "test-user-456",
    }


class TestHealthCheck:
    """Health check endpoint tests."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestMultiTenancy:
    """Multi-tenant isolation tests."""

    def test_missing_tenant_header(self, client):
        """Request without tenant header should fail."""
        response = client.post(
            "/api/v1/query",
            json={"query": "test"},
        )
        assert response.status_code == 400

    def test_tenant_isolation(self, client, test_tenant):
        """Different tenants should not see each other's data."""
        headers_1 = {
            "X-Tenant-ID": "tenant-1",
            "X-User-ID": "user-1",
        }
        headers_2 = {
            "X-Tenant-ID": "tenant-2",
            "X-User-ID": "user-1",
        }

        # Both requests should succeed but be isolated
        response1 = client.post(
            "/api/v1/query",
            json={"query": "test query"},
            headers=headers_1,
        )
        response2 = client.post(
            "/api/v1/query",
            json={"query": "test query"},
            headers=headers_2,
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Query IDs should be different
        query_1 = response1.json()["query_id"]
        query_2 = response2.json()["query_id"]
        assert query_1 != query_2


class TestQueryEndpoint:
    """Query execution endpoint tests."""

    def test_query_response_schema(self, client, test_tenant):
        """Verify response contains all required fields."""
        headers = {
            "X-Tenant-ID": test_tenant["tenant_id"],
            "X-User-ID": test_tenant["user_id"],
        }

        response = client.post(
            "/api/v1/query",
            json={
                "query": "What is the capital of France?",
                "top_k": 5,
                "include_trace": True,
            },
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify schema
        assert "query_id" in data
        assert "response" in data
        assert "retrieved_documents" in data
        assert "metrics" in data
        assert "trace_id" in data

        # Verify metrics
        metrics = data["metrics"]
        assert "total_latency_ms" in metrics
        assert "retrieval_latency_ms" in metrics
        assert "llm_latency_ms" in metrics
        assert "input_tokens" in metrics
        assert "output_tokens" in metrics
        assert "cost_usd" in metrics

    def test_ab_variant_routing(self, client, test_tenant):
        """Verify A/B variant parameter is respected."""
        headers = {
            "X-Tenant-ID": test_tenant["tenant_id"],
            "X-User-ID": test_tenant["user_id"],
        }

        # Test variant_a
        response_a = client.post(
            "/api/v1/query?ab_variant=variant_a",
            json={"query": "test"},
            headers=headers,
        )
        assert response_a.json()["metrics"]["ab_variant"] == "variant_a"

        # Test variant_b
        response_b = client.post(
            "/api/v1/query?ab_variant=variant_b",
            json={"query": "test"},
            headers=headers,
        )
        assert response_b.json()["metrics"]["ab_variant"] == "variant_b"


class TestDocumentUpload:
    """Document upload endpoint tests."""

    def test_upload_document(self, client, test_tenant):
        """Test document upload functionality."""
        headers = {
            "X-Tenant-ID": test_tenant["tenant_id"],
            "X-User-ID": test_tenant["user_id"],
        }

        # Create mock file
        file_content = b"This is a test document with some content."
        files = {"file": ("test.txt", file_content, "text/plain")}

        response = client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert data["filename"] == "test.txt"
        assert data["chunks_created"] > 0
        assert data["status"] == "success"


class TestDashboardEndpoints:
    """Dashboard API endpoints tests."""

    def test_dashboard_overview(self, client, test_tenant):
        """Test dashboard overview metrics."""
        headers = {
            "X-Tenant-ID": test_tenant["tenant_id"],
            "X-User-ID": test_tenant["user_id"],
        }

        response = client.get(
            "/api/v1/dashboard/overview",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "kpis" in data
        assert "total_queries" in data["kpis"]
        assert "hallucination_rate" in data["kpis"]

    def test_cost_tracking(self, client, test_tenant):
        """Test cost tracking endpoint."""
        headers = {
            "X-Tenant-ID": test_tenant["tenant_id"],
            "X-User-ID": test_tenant["user_id"],
        }

        response = client.get(
            "/api/v1/dashboard/cost-tracking?days=30",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_cost_usd" in data
        assert "by_model" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
