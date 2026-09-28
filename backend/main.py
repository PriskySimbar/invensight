"""InvenSight AI — FastAPI entrypoint."""

from __future__ import annotations

import time
import os
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from graph import run_analyze
from rate_limiter import check_rate_limit
from redis_client import cache_service
from rag_system import rag_system, rag_metrics
from vision_system import vision_system

app = FastAPI(title="InvenSight AI", version="0.2.0")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# Performance metrics storage
performance_metrics = {
    "total_requests": 0,
    "total_errors": 0,
    "total_response_time": 0,
    "cache_hits": 0,
    "cache_misses": 0,
}

# Custom rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    return HTTPException(
        status_code=429,
        detail={
            "error": "Rate limit exceeded",
            "message": "Too many requests. Please try again later.",
        }
    )

# Frontend Next.js (App Router) di development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)


class AnalyzeRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Pertanyaan analitik gudang")


class AnalyzeResponse(BaseModel):
    sql_query: str
    data: list[dict]
    summary: str
    is_error: bool


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Pertanyaan tentang dokumen")


class RAGQueryResponse(BaseModel):
    answer: str
    source_chunks: list


class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    chunks_count: int


class VisionAnalysisResponse(BaseModel):
    success: bool
    analysis: str
    extracted_text: str
    metadata: dict


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
def analyze(body: AnalyzeRequest, request: Request) -> AnalyzeResponse:
    start_time = time.time()
    performance_metrics["total_requests"] += 1
    
    # Check cache first (synchronous for now)
    cache_key = f"analyze:{body.question}"
    cached_result = None  # await cache_service.get(cache_key)
    
    if cached_result:
        performance_metrics["cache_hits"] += 1
        return AnalyzeResponse(**cached_result)
    
    performance_metrics["cache_misses"] += 1
    
    try:
        result = run_analyze(body.question)
        
        # Cache the result for 5 minutes (synchronous for now)
        # await cache_service.set(cache_key, result, ttl=300)
        
    except RuntimeError as exc:
        performance_metrics["total_errors"] += 1
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # Groq / DB / graph
        performance_metrics["total_errors"] += 1
        raise HTTPException(status_code=502, detail=f"Gagal menjalankan agent: {exc}") from exc

    performance_metrics["total_response_time"] += (time.time() - start_time)
    return AnalyzeResponse(**result)


@app.get("/api/v1/metrics")
def get_metrics() -> dict:
    """Get performance metrics for monitoring."""
    total_requests = performance_metrics["total_requests"]
    avg_response_time = (
        performance_metrics["total_response_time"] / total_requests 
        if total_requests > 0 else 0
    )
    error_rate = (
        performance_metrics["total_errors"] / total_requests 
        if total_requests > 0 else 0
    )
    cache_hit_rate = (
        performance_metrics["cache_hits"] / (performance_metrics["cache_hits"] + performance_metrics["cache_misses"])
        if (performance_metrics["cache_hits"] + performance_metrics["cache_misses"]) > 0 else 0
    )
    
    # Simple cost metrics
    cost_metrics = {
        "total_requests": total_requests,
        "total_tokens": 0,  # Add token tracking
        "total_cost_usd": "$0.0000",
        "avg_tokens_per_request": 0,
        "avg_cost_per_request": 0,
    }
    
    return {
        "performance": {
            "total_requests": total_requests,
            "total_errors": performance_metrics["total_errors"],
            "error_rate": f"{error_rate:.2%}",
            "average_response_time": f"{avg_response_time:.3f}s",
            "cache_hits": performance_metrics["cache_hits"],
            "cache_misses": performance_metrics["cache_misses"],
            "cache_hit_rate": f"{cache_hit_rate:.2%}",
            "redis_enabled": cache_service.enabled,
        },
        "cost": cost_metrics,
        "rag": {
            "cache_hits": rag_metrics["cache_hits"],
            "cache_misses": rag_metrics["cache_misses"],
        }
    }


# RAG endpoints (simplified mode)
@app.post("/api/v1/documents/upload", response_model=DocumentUploadResponse)
@limiter.limit("5/minute")
async def upload_document(request: Request, file: UploadFile = File(...)):
    """Upload PDF document for RAG processing."""
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Process PDF
        text = rag_system.load_pdf(temp_path)
        chunks = rag_system.chunk_text(text)
        
        # Create vector store (simplified)
        rag_system.create_vector_store(chunks)
        rag_system.setup_qa_chain()
        
        # Clean up temp file
        import os
        os.remove(temp_path)
        
        return DocumentUploadResponse(
            success=True,
            message=f"Document processed successfully. {len(chunks)} chunks created.",
            chunks_count=len(chunks)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@app.post("/api/v1/rag/query", response_model=RAGQueryResponse)
@limiter.limit("10/minute")
async def rag_query(request: Request, body: RAGQueryRequest):
    """Query uploaded documents using RAG."""
    try:
        result = rag_system.query(body.question)
        return RAGQueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")


@app.post("/api/v1/vision/analyze", response_model=VisionAnalysisResponse)
@limiter.limit("5/minute")
async def analyze_vision(request: Request, file: UploadFile = File(...)):
    """Analyze uploaded image using OCR and vision."""
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_vision_{file.filename}"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Analyze image
        analysis_result = vision_system.analyze_inventory_image(temp_path)
        
        # Clean up temp file
        import os
        os.remove(temp_path)
        
        return VisionAnalysisResponse(
            success=analysis_result.get("success", False),
            analysis=analysis_result.get("analysis", ""),
            extracted_text=analysis_result.get("extracted_text", ""),
            metadata=analysis_result.get("metadata", {})
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vision analysis failed: {str(e)}")
