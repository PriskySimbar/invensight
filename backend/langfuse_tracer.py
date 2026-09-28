"""
Langfuse integration for AI observability and cost tracking.
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langfuse import Langfuse
from tiktoken import encoding_for_model

load_dotenv()

class LangfuseTracer:
    """Langfuse tracer for AI observability."""
    
    def __init__(self):
        self.enabled = bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))
        if self.enabled:
            self.langfuse = Langfuse(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
            )
        else:
            self.langfuse = None
    
    def create_trace(self, name: str, user_id: Optional[str] = None, metadata: Optional[Dict] = None):
        """Create a new trace."""
        if not self.enabled:
            return None
        
        return self.langfuse.trace(
            name=name,
            user_id=user_id,
            metadata=metadata or {}
        )
    
    def create_span(self, trace, name: str, metadata: Optional[Dict] = None):
        """Create a new span within a trace."""
        if not self.enabled or not trace:
            return None
        
        return trace.span(
            name=name,
            metadata=metadata or {}
        )
    
    def end_span(self, span, output: Optional[Dict] = None):
        """End a span with optional output."""
        if not self.enabled or not span:
            return
        
        span.end(output=output)
    
    def end_trace(self, trace, output: Optional[Dict] = None):
        """End a trace with optional output."""
        if not self.enabled or not trace:
            return
        
        trace.end(output=output)
    
    def flush(self):
        """Flush all traces to Langfuse."""
        if self.enabled and self.langfuse:
            self.langfuse.flush()

class CostTracker:
    """Cost tracker for API usage."""
    
    def __init__(self):
        self.enabled = os.getenv("COST_TRACKING_ENABLED", "false").lower() == "true"
        self.costs = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "requests": 0
        }
        
        # Cost per token (approximate for Groq Llama models)
        self.cost_per_token = 0.000001  # $0.001 per 1M tokens (approximate)
    
    def count_tokens(self, text: str, model: str = "llama-3.3-70b-versatile") -> int:
        """Count tokens in text using tiktoken."""
        try:
            # Use cl100k_base encoding as approximation for most models
            encoding = encoding_for_model("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            print(f"Token counting error: {e}")
            # Fallback: rough estimate (4 chars per token)
            return len(text) // 4
    
    def track_request(self, input_text: str, output_text: str, model: str = "llama-3.3-70b-versatile"):
        """Track cost for a request."""
        if not self.enabled:
            return
        
        input_tokens = self.count_tokens(input_text, model)
        output_tokens = self.count_tokens(output_text, model)
        total_tokens = input_tokens + output_tokens
        
        cost = total_tokens * self.cost_per_token
        
        self.costs["total_tokens"] += total_tokens
        self.costs["total_cost"] += cost
        self.costs["requests"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cost metrics."""
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

# Global instances
langfuse_tracer = LangfuseTracer()
cost_tracker = CostTracker()
