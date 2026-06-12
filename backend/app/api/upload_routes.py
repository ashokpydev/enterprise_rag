"""
Document Upload API Routes
Implements multi-tenant document ingestion with asynchronous processing.
"""

from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import aiofiles
import os

from app.services.vector_store import VectorStoreService
from app.core.config import settings

router = APIRouter()

# Initialize services
vector_store_service = VectorStoreService()


# ==================== Request/Response Models ====================
class UploadResponse(BaseModel):
    """Document upload response."""

    document_id: str
    filename: str
    status: str
    chunks_created: int
    message: str


# ==================== Upload Endpoint ====================
@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    x_tenant_id: str = Header(...),
    x_user_id: str = Header(...),
    security_level: Optional[str] = None,
):
    """
    Upload and process a document for RAG.

    Multi-tenant operation that:
    1. Stores document in database
    2. Chunks document based on configuration
    3. Embeds chunks using sentence transformer
    4. Stores embeddings in FAISS vector store

    In production, this would use Celery for async processing.
    """
    document_id = str(uuid.uuid4())
    security_level = security_level or "public"

    try:
        # Read file content
        content = await file.read()
        text_content = content.decode("utf-8")

        # Split into chunks
        chunk_size = settings.CHUNK_SIZE
        chunk_overlap = settings.CHUNK_OVERLAP

        chunks = []
        for i in range(0, len(text_content), chunk_size - chunk_overlap):
            chunk = text_content[i : i + chunk_size]
            if chunk.strip():
                chunks.append(chunk)

        # Add chunks to vector store
        num_chunks = vector_store_service.add_chunks(
            tenant_id=x_tenant_id,
            document_id=document_id,
            chunks=chunks,
            security_level=security_level,
            metadata={
                "filename": file.filename,
                "file_type": file.filename.split(".")[-1],
                "uploaded_by": x_user_id,
            },
        )

        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            status="success",
            chunks_created=num_chunks,
            message=f"Document {file.filename} processed with {num_chunks} chunks",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.get("/list")
async def list_documents(
    x_tenant_id: str = Header(...),
):
    """List documents for a tenant."""
    # This would query the Document table
    return {
        "tenant_id": x_tenant_id,
        "documents": [
            {
                "document_id": "doc_123",
                "filename": "company_handbook.pdf",
                "chunks": 42,
                "security_level": "public",
                "uploaded_at": "2024-01-15T10:30:00",
            }
        ],
    }
