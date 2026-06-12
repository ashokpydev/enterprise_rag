"""
RAG Retrieval Service
Orchestrates retrieval pipeline with full observability.
Implements hybrid search, re-ranking, and quality metrics.
"""

import time
from typing import List, Tuple, Optional, Dict, Any

from app.services.vector_store import VectorStoreService, RerankerService
from app.telemetry.otel import record_rag_span, RAGSpanAttributes
from app.core.config import settings


class RAGRetrievalService:
    """
    Orchestrates the complete retrieval pipeline.
    - Vector search + metadata filtering
    - Cross-encoder re-ranking
    - Context quality evaluation
    """

    def __init__(self):
        self.vector_store = VectorStoreService()
        self.reranker = RerankerService()

    def retrieve(
        self,
        query: str,
        tenant_id: str,
        user_id: str,
        user_security_level: Optional[str] = None,
        top_k: int = 5,
        ab_variant: str = "variant_a",
    ) -> Dict[str, Any]:
        """
        Full retrieval pipeline with observability.

        Args:
            query: User query
            tenant_id: Tenant identifier
            user_id: User identifier
            user_security_level: RBAC security level to filter by
            top_k: Number of results
            ab_variant: A/B testing variant

        Returns:
            Dict with retrieved chunks, scores, and metrics
        """
        retrieval_start = time.time()

        # ==================== Step 1: Vector Search ====================
        with record_rag_span(
            "vector_search",
            RAGSpanAttributes.retrieval_span(
                tenant_id=tenant_id,
                user_id=user_id,
                query=query,
                documents_retrieved=0,  # Will update
                retrieval_latency_ms=0,  # Will update
            ),
        ) as search_span:
            search_start = time.time()

            texts, scores, metadata = self.vector_store.search(
                query=query,
                tenant_id=tenant_id,
                top_k=top_k * 2,  # Get extra for re-ranking
                security_level=user_security_level,
            )

            search_latency_ms = (time.time() - search_start) * 1000
            search_span.set_attribute("retrieval.latency_ms", search_latency_ms)
            search_span.set_attribute("retrieval.documents_returned", len(texts))
            search_span.set_attribute("ab_variant", ab_variant)

        # ==================== Step 2: Re-ranking ====================
        rerank_start = time.time()
        with record_rag_span(
            "cross_encoder_reranking",
            RAGSpanAttributes.reranking_span(
                original_rank_count=len(texts),
                reranked_count=top_k,
                reranking_latency_ms=0,  # Will update
            ),
        ) as rerank_span:
            if texts:
                texts, rerank_scores = self.reranker.rerank(query=query, documents=texts, top_k=top_k)

                rerank_latency_ms = (time.time() - rerank_start) * 1000
                rerank_span.set_attribute("reranking.latency_ms", rerank_latency_ms)
                rerank_span.set_attribute("reranking.top_scores", [float(s) for s in rerank_scores])

        total_retrieval_latency_ms = (time.time() - retrieval_start) * 1000

        return {
            "texts": texts,
            "scores": rerank_scores if texts else [],
            "count": len(texts),
            "latency_ms": total_retrieval_latency_ms,
            "search_latency_ms": search_latency_ms,
            "rerank_latency_ms": rerank_latency_ms,
            "metadata": metadata[:len(texts)],
        }


class LLMCompletionService:
    """
    LLM completion with token tracking for cost attribution.
    """

    def __init__(self):
        from app.services.llm_provider import LLMProvider

        self.llm_provider = LLMProvider()

    def generate_response(
        self,
        query: str,
        context_docs: List[str],
        tenant_id: str,
        user_id: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate LLM response with context and track metrics.

        Args:
            query: User query
            context_docs: Retrieved context documents
            tenant_id: Tenant identifier
            user_id: User identifier
            temperature: Generation temperature
            max_tokens: Max output tokens

        Returns:
            Dict with response, tokens, latency, and cost
        """
        temperature = temperature or settings.TEMPERATURE
        max_tokens = max_tokens or settings.MAX_TOKENS

        with record_rag_span(
            "llm_completion",
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "model": settings.OPENAI_MODEL,
            },
        ) as llm_span:
            completion_start = time.time()

            # Build prompt with context
            prompt = self._build_rag_prompt(query, context_docs)

            # Get completion
            response = self.llm_provider.complete(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            llm_latency_ms = (time.time() - completion_start) * 1000

            # Extract token counts
            input_tokens = response.get("usage", {}).get("prompt_tokens", 0)
            output_tokens = response.get("usage", {}).get("completion_tokens", 0)
            total_tokens = input_tokens + output_tokens

            # Calculate cost (OpenAI pricing)
            cost_usd = self._calculate_cost(
                model=settings.OPENAI_MODEL,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )

            # Record metrics
            llm_span.set_attributes(
                RAGSpanAttributes.llm_span(
                    model=settings.OPENAI_MODEL,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    latency_ms=llm_latency_ms,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tenant_id=tenant_id,
                    cost_usd=cost_usd,
                )
            )

            return {
                "response": response.get("choices", [{}])[0].get("text", ""),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "latency_ms": llm_latency_ms,
                "cost_usd": cost_usd,
                "model": settings.OPENAI_MODEL,
            }

    def _build_rag_prompt(self, query: str, context_docs: List[str]) -> str:
        """Build RAG prompt with context."""
        context_text = "\n\n".join(
            [f"[Document {i+1}]\n{doc}" for i, doc in enumerate(context_docs)]
        )

        prompt = f"""You are a helpful assistant. Use the following context to answer the user's question.

Context:
{context_text}

Question: {query}

Answer:"""
        return prompt

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate API cost based on token usage."""
        # OpenAI pricing (as of Nov 2024)
        pricing = {
            "gpt-4-turbo-preview": {"input": 0.01 / 1000, "output": 0.03 / 1000},
            "gpt-3.5-turbo": {"input": 0.0005 / 1000, "output": 0.0015 / 1000},
            "gpt-4": {"input": 0.03 / 1000, "output": 0.06 / 1000},
        }

        rates = pricing.get(model, {"input": 0.01 / 1000, "output": 0.03 / 1000})
        return input_tokens * rates["input"] + output_tokens * rates["output"]
