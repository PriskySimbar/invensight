"""
RAG System for document processing and retrieval.
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Local metrics for RAG system  
rag_metrics = {
    "cache_hits": 0,
    "cache_misses": 0,
}

class RAGSystem:
    """RAG system for document Q&A."""
    
    def __init__(self):
        self.chunks = []
        self.enabled = False
        self.llm = None
        self.document_loaded = False
        
        # Try to initialize LLM
        try:
            from langchain_groq import ChatGroq
            self.llm = ChatGroq(
                model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
                api_key=os.getenv("GROQ_API_KEY"),
                temperature=0.1
            )
            self.enabled = True
            print("RAG System initialized (simplified mode)")
            
            # Auto-load sample PDF if exists
            self.load_sample_document()
            
        except Exception as e:
            print(f"RAG System initialization failed: {e}")
    
    def load_sample_document(self):
        """Auto-load sample PDF if available."""
        sample_pdf = "sample_warehouse_sop.pdf"
        # Try multiple paths
        paths_to_try = [
            sample_pdf,  # Current directory
            f"../frontend/public/{sample_pdf}",  # Parent frontend/public
            f"frontend/public/{sample_pdf}",  # Relative frontend/public
        ]
        
        for path in paths_to_try:
            if os.path.exists(path):
                print(f"Auto-loading sample document: {path}")
                text = self.load_pdf(path)
                chunks = self.chunk_text(text)
                self.create_vector_store(chunks)
                self.setup_qa_chain()
                self.document_loaded = True
                print(f"Sample document loaded with {len(chunks)} chunks")
                return
        
        print("No sample PDF found - document will be empty until upload")
    
    def load_pdf(self, pdf_path: str) -> str:
        """Load and extract text from PDF."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            return f"Error loading PDF: {str(e)}"
    
    def chunk_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """Split text into chunks."""
        # Simple chunking without LangChain dependencies
        chunks = []
        for i in range(0, len(text), chunk_size - chunk_overlap):
            chunk = text[i:i + chunk_size]
            if chunk:
                chunks.append(chunk)
        return chunks
    
    def create_vector_store(self, chunks: List[str]):
        """Store chunks (simplified mode without vector DB)."""
        self.chunks = chunks
        print(f"Stored {len(chunks)} chunks for RAG")
    
    def setup_qa_chain(self, vector_store=None):
        """Setup RAG (simplified mode)."""
        # In simplified mode, we'll search chunks directly
        pass
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the RAG system (simplified mode)."""
        rag_metrics["cache_misses"] += 1
        
        if not self.chunks:
            return {
                "answer": "No documents loaded. Please upload a PDF first.",
                "source_chunks": []
            }
        
        # Simple keyword search
        question_words = set(word.lower() for word in question.split())
        relevant_chunks = []
        
        for chunk in self.chunks:
            chunk_words = set(word.lower() for word in chunk.split())
            # Calculate similarity
            overlap = len(question_words & chunk_words)
            if overlap > 0:
                relevant_chunks.append((chunk, overlap))
        
        # Sort by relevance and take top 3
        relevant_chunks.sort(key=lambda x: x[1], reverse=True)
        top_chunks = [chunk[0] for chunk in relevant_chunks[:3]]
        
        if not top_chunks:
            return {
                "answer": "I couldn't find relevant information in the document. Please try a different question.",
                "source_chunks": []
            }
        
        context = "\n\n".join(top_chunks)
        
        # Use LLM to generate answer
        if self.llm:
            try:
                prompt = f"""
                Based on the following context from a warehouse SOP document, answer the question concisely.
                
                Context:
                {context}
                
                Question: {question}
                
                Answer:
                """
                
                response = self.llm.invoke(prompt)
                answer = response.content if hasattr(response, 'content') else str(response)
                
                return {
                    "answer": answer,
                    "source_chunks": top_chunks
                }
                
            except Exception as e:
                return {
                    "answer": f"Error generating answer: {str(e)}",
                    "source_chunks": top_chunks
                }
        else:
            # Fallback without LLM
            return {
                "answer": f"Found {len(top_chunks)} relevant sections in the document. LLM not available to generate detailed answer.",
                "source_chunks": top_chunks
            }

# Global RAG system instance
rag_system = RAGSystem()
