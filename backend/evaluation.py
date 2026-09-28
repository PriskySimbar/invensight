"""
RAG evaluation using RAGAS/DeepEval.
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class RAGEvaluator:
    """RAG evaluation using DeepEval."""
    
    def __init__(self):
        self.enabled = os.getenv("RAG_EVALUATION_ENABLED", "false").lower() == "true"
        if self.enabled:
            try:
                from deepeval import evaluate
                from deepeval.metrics import Faithfulness, AnswerRelevancy
                from deepeval.test_case import LLMTestCase
                
                self.evaluate = evaluate
                self.Faithfulness = Faithfulness
                self.AnswerRelevancy = AnswerRelevancy
                self.LLMTestCase = LLMTestCase
            except ImportError:
                self.enabled = False
    
    def evaluate_response(
        self, 
        question: str, 
        answer: str, 
        context: List[str],
        expected_answer: str = None
    ) -> Dict[str, Any]:
        """Evaluate RAG response quality."""
        if not self.enabled:
            return {
                "faithfulness": "N/A",
                "answer_relevancy": "N/A",
                "message": "Evaluation disabled"
            }
        
        try:
            # Create test case
            test_case = self.LLMTestCase(
                input=question,
                actual_output=answer,
                retrieval_context=context,
                expected_output=expected_answer or ""
            )
            
            # Initialize metrics
            faithfulness_metric = self.Faithfulness()
            relevancy_metric = self.AnswerRelevancy()
            
            # Evaluate
            faithfulness_metric.measure(test_case)
            relevancy_metric.measure(test_case)
            
            return {
                "faithfulness": faithfulness_metric.score,
                "answer_relevancy": relevancy_metric.score,
                "faithfulness_passed": faithfulness_metric.is_successful(),
                "relevancy_passed": relevancy_metric.is_successful(),
                "message": "Evaluation completed"
            }
            
        except Exception as e:
            return {
                "faithfulness": "Error",
                "answer_relevancy": "Error",
                "message": f"Evaluation failed: {str(e)}"
            }

# Global evaluator instance
rag_evaluator = RAGEvaluator()
