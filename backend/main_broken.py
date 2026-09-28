"""InvenSight AI — FastAPI entrypoint."""

from __future__ import annotations

import time
import os
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from graph import run_analyze
from rate_limiter import check_rate_limit
from redis_client import cache_service
# Temporarily disable RAG and vision due to dependency issues
# from rag_system import rag_system, rag_metrics
# from vision_system import vision_system
# Temporarily disable Langfuse due to import issues
# from langfuse_tracer import langfuse_tracer, cost_tracker

# Simple cost tracker without external dependencies
class SimpleCostTracker:
    def __init__(self):
        self.costs = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "requests": 0
        }
        self.cost_per_token = 0.000001  # Approximate cost
    
    def track_request(self, input_text: str, output_text: str, model: str = "llama-3.3-70b-versatile"):
        # Simple token counting (4 chars per token approximation)
        input_tokens = len(input_text) // 4
        output_tokens = len(output_text) // 4
        total_tokens = input_tokens + output_tokens
        cost = total_tokens * self.cost_per_token
        
        self.costs["total_tokens"] += total_tokens
        self.costs["total_cost"] += cost
        self.costs["requests"] += 1
    
    def get_metrics(self):
        return {
            "total_requests": self.costs["requests"],
            "total_tokens": self.costs["total_tokens"],
            "total_cost_usd": f"${self.costs['total_cost']:.4f}",
            "avg_tokens_per_request": (
                self.costs["total_tokens"] / self.costs["requests"]
                if self.costs["requests"] > 0 else 0
            ),
            "avg_cost_per_request": (
                self.costs["total_cost"] / self.costs["requests"]
                if self.costs["requests"] > 0 else 0
            )
        }

class SimpleLangfuseTracer:
    def __init__(self):
        self.enabled = False
    
    def create_trace(self, name, user_id=None, metadata=None):
        return None
    
    def end_trace(self, trace, output=None):
        pass

langfuse_tracer = SimpleLangfuseTracer()
cost_tracker = SimpleCostTracker()

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


# Temporarily disabled due to dependency issues
# class VisionAnalysisRequest(BaseModel):
#     question: str = Field(..., description="Question about the image")
# 
# 
# class VisionAnalysisResponse(BaseModel):
#     success: bool
#     analysis: str
#     extracted_text: str
#     metadata: dict


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
def analyze(body: AnalyzeRequest, request: Request) -> AnalyzeResponse:
    start_time = time.time()
    performance_metrics["total_requests"] += 1
    
    # Create Langfuse trace
    trace = langfuse_tracer.create_trace(
        name="warehouse_analyze",
        user_id=request.client.host if request.client else "anonymous",
        metadata={"question": body.question}
    )
    
    # Check cache first (synchronous for now)
    cache_key = f"analyze:{body.question}"
    cached_result = None  # await cache_service.get(cache_key)
    
    if cached_result:
        performance_metrics["cache_hits"] += 1
        if trace:
            langfuse_tracer.end_trace(trace, {"cached": True, "response_time": time.time() - start_time})
        return AnalyzeResponse(**cached_result)
    
    performance_metrics["cache_misses"] += 1
    
    try:
        result = run_analyze(body.question)
        
        # Track cost
        cost_tracker.track_request(
            input_text=body.question,
            output_text=result.get("summary", ""),
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        )
        
        # Cache the result for 5 minutes (synchronous for now)
        # await cache_service.set(cache_key, result, ttl=300)
        
        if trace:
            langfuse_tracer.end_trace(trace, {
                "cached": False,
                "response_time": time.time() - start_time,
                "sql_query": result.get("sql_query", ""),
                "data_rows": len(result.get("data", []))
            })
        
    except RuntimeError as exc:
        performance_metrics["total_errors"] += 1
        if trace:
            langfuse_tracer.end_trace(trace, {"error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # Groq / DB / graph
        performance_metrics["total_errors"] += 1
        if trace:
            langfuse_tracer.end_trace(trace, {"error": str(exc)})
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
    
    # Include cost metrics
    cost_metrics = cost_tracker.get_metrics()
    
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
    }


@app.post("/api/v1/documents/upload", response_model=DocumentUploadResponse)
@limiter.limit("5/minute")
async def upload_document(file: UploadFile = File(...)):
    """Upload PDF document for RAG processing."""
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Process PDF
        text = rag_system.load_pdf(temp_path)
        chunks = rag_system.chunk_text(text)
        
        # Create vector store
        vector_store = rag_system.create_vector_store(chunks)
        rag_system.setup_qa_chain(vector_store)
        
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


# Temporarily disabled RAG endpoints due to dependency issues
# @app.post("/api/v1/documents/upload", response_model=DocumentUploadResponse)
# @limiter.limit("5/minute")
# async def upload_document(file: UploadFile = File(...)):
#     """Upload PDF document for RAG processing."""
#     try:
#         # Save uploaded file temporarily
#         temp_path = f"temp_{file.filename}"
#         with open(temp_path, "wb") as buffer:
#             buffer.write(await file.read())
#         
#         # Process PDF
#         text = rag_system.load_pdf(temp_path)
#         chunks = rag_system.chunk_text(text)
#         
#         # Create vector store
#         vector_store = rag_system.create_vector_store(chunks)
#         rag_system.setup_qa_chain(vector_store)
#         
#         # Clean up temp file
#         import os
#         os.remove(temp_path)
#         
#         return DocumentUploadResponse(
#             success=True,
#             message=f"Document processed successfully. {len(chunks)} chunks created.",
#             chunks_count=len(chunks)
#         )
#         
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


# @app.post("/api/v1/rag/query", response_model=RAGQueryResponse)
# @limiter.limit("10/minute")
# async def rag_query(body: RAGQueryRequest):
#     """Query uploaded documents using RAG."""
#     try:
#         result = rag_system.query(body.question)
#         return RAGQueryResponse(**result)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")


# @app.post("/api/v1/vision/analyze", response_model=VisionAnalysisResponse)
# @limiter.limit("5/minute")
# async def analyze_vision(file: UploadFile = File(...), question: str = ""):
#     """Analyze uploaded image using OCR and vision."""
#     try:
#         # Save uploaded file temporarily
#         temp_path = f"temp_vision_{file.filename}"
#         with open(temp_path, "wb") as buffer:
#             buffer.write(await file.read())
#         
#         # Analyze image
#         analysis_result = vision_system.analyze_inventory_image(temp_path)
#         
#         # Clean up temp file
#         import os
#         os.remove(temp_path)
#         
#         return VisionAnalysisResponse(
#             success=analysis_result.get("success", False),
#             analysis=analysis_result.get("analysis", ""),
#             extracted_text=analysis_result.get("extracted_text", ""),
#             metadata={
#                 "dimensions": analysis_result.get("image_dimensions", {}),
#                 "box_estimate": analysis_result.get("box_count_estimate", 0)
#             }
#         )
#         
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Vision analysis failed: {str(e)}")
