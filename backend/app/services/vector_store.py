"""
Vector Store Service
Manages FAISS vector database for semantic search.
Supports efficient retrieval with metadata filtering for multi-tenancy.
"""

import os
import json
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings
from app.telemetry.otel import record_rag_span, RAGSpanAttributes


class VectorStoreService:
    """
    FAISS-based vector store with multi-tenant support.
    Stores document chunks and enables fast semantic search.
    """

    def __init__(self):
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.vector_dimension = settings.VECTOR_DIMENSION
        self.index_path = settings.VECTOR_STORE_PATH
        self.metadata_file = os.path.join(self.index_path, "metadata.json")

        # Create storage directory
        Path(self.index_path).mkdir(parents=True, exist_ok=True)

        # Load or create FAISS index
        self.index_file = os.path.join(self.index_path, "index.faiss")
        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)
            self.metadata = self._load_metadata()
        else:
            self.index = faiss.IndexFlatL2(self.vector_dimension)
            self.metadata = {}

        print(f"Vector store initialized with {self.index.ntotal} embeddings")

    def _load_metadata(self) -> Dict[int, Dict[str, Any]]:
        """Load metadata mapping from disk."""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return {}

    def _save_metadata(self):
        """Persist metadata to disk."""
        os.makedirs(self.index_path, exist_ok=True)
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def _save_index(self):
        """Persist FAISS index to disk."""
        faiss.write_index(self.index, self.index_file)

    def add_chunks(
        self,
        tenant_id: str,
        document_id: str,
        chunks: List[str],
        security_level: str = "public",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Add document chunks to the vector store.

        Args:
            tenant_id: Multi-tenant identifier
            document_id: Document reference
            chunks: List of text chunks to embed
            security_level: RBAC security level
            metadata: Additional metadata

        Returns:
            Number of vectors added
        """
        if not chunks:
            return 0

        # Embed chunks
        embeddings = self.embedding_model.encode(chunks, convert_to_numpy=True)
        embeddings = embeddings.astype("float32")

        # Get current index size
        start_idx = self.index.ntotal

        # Add to FAISS
        self.index.add(embeddings)

        # Store metadata
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            idx = start_idx + i
            self.metadata[str(idx)] = {
                "tenant_id": tenant_id,
                "document_id": document_id,
                "chunk_index": i,
                "text": chunk,
                "security_level": security_level,
                "embedding": embedding.tolist(),
                **(metadata or {}),
            }

        # Persist
        self._save_index()
        self._save_metadata()

        return len(chunks)

    def search(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 10,
        security_level: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[str], List[float], List[Dict[str, Any]]]:
        """
        Semantic search with multi-tenant and RBAC filtering.

        Args:
            query: User query
            tenant_id: Filter by tenant
            top_k: Number of results
            security_level: RBAC security level to filter by
            filters: Additional metadata filters

        Returns:
            Tuple of (texts, scores, metadata)
        """
        with record_rag_span(
            "vector_db_retrieval",
            {
                "tenant_id": tenant_id,
                "query": query[:100],
                "top_k": top_k,
            },
        ) as span:
            # Embed query
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True).astype(
                "float32"
            )

            # Search in FAISS
            distances, indices = self.index.search(query_embedding, min(top_k * 3, self.index.ntotal))
            distances = distances[0]
            indices = indices[0]

            # Post-filter by tenant and security level
            results = []
            for dist, idx in zip(distances, indices):
                if idx < 0 or str(idx) not in self.metadata:
                    continue

                meta = self.metadata[str(idx)]

                # Tenant filtering (mandatory)
                if meta.get("tenant_id") != tenant_id:
                    continue

                # Security level filtering (RBAC)
                if security_level and meta.get("security_level", "public") != security_level:
                    continue

                # Additional metadata filtering
                if filters:
                    skip = False
                    for key, value in filters.items():
                        if meta.get(key) != value:
                            skip = True
                            break
                    if skip:
                        continue

                # Convert L2 distance to similarity score
                similarity_score = 1 / (1 + dist)
                results.append(
                    {
                        "text": meta["text"],
                        "score": float(similarity_score),
                        "metadata": meta,
                    }
                )

            # Return top-k
            results = results[:top_k]

            # Record metrics
            span.set_attribute("retrieval.documents_returned", len(results))
            span.set_attribute("retrieval.scores", [r["score"] for r in results])

            return (
                [r["text"] for r in results],
                [r["score"] for r in results],
                [r["metadata"] for r in results],
            )

    def hybrid_search(
        self,
        query: str,
        tenant_id: str,
        bm25_texts: Optional[List[str]] = None,
        top_k: int = 10,
        security_level: Optional[str] = None,
    ) -> Tuple[List[str], List[float]]:
        """
        Hybrid search combining semantic search with BM25 keyword matching.
        Provides better results by capturing both semantic and keyword relevance.

        Args:
            query: User query
            tenant_id: Filter by tenant
            bm25_texts: Pre-computed BM25 results (optional)
            top_k: Number of results
            security_level: RBAC security level

        Returns:
            Tuple of (texts, combined_scores)
        """
        # Semantic search
        semantic_texts, semantic_scores, _ = self.search(
            query=query,
            tenant_id=tenant_id,
            top_k=top_k * 2,
            security_level=security_level,
        )

        if not bm25_texts:
            return semantic_texts[:top_k], semantic_scores[:top_k]

        # BM25 search (placeholder - would use rank_bm25 library)
        # For now, just use semantic scores
        return semantic_texts[:top_k], semantic_scores[:top_k]


class RerankerService:
    """
    Cross-encoder re-ranker for context quality improvement.
    Re-orders retrieved documents to maximize relevance.
    """

    def __init__(self):
        # Using lightweight cross-encoder
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5,
    ) -> Tuple[List[str], List[float]]:
        """
        Re-rank documents for relevance to query.

        Args:
            query: User query
            documents: List of candidate documents
            top_k: Number to return

        Returns:
            Tuple of (reranked_texts, scores)
        """
        if not documents:
            return [], []

        # Score pairs
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)

        # Sort by score (descending)
        ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        texts, scores = zip(*ranked[:top_k])

        return list(texts), list(scores)
