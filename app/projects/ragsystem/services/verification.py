"""
Chain-of-Verification Service
Reduces hallucinations through multi-step verification
"""
from typing import List, Dict, Any
import logging
import re

from ..config import rag_config
from ..models import RetrievedChunk, VerificationStep

logger = logging.getLogger(__name__)


class VerificationService:
    """Chain-of-Verification implementation"""
    
    def __init__(self):
        self.enabled = rag_config.COVE_ENABLED
        self.num_steps = rag_config.COVE_VERIFICATION_STEPS
        self.confidence_threshold = rag_config.COVE_CONFIDENCE_THRESHOLD
    
    async def verify(
        self,
        query: str,
        answer: str,
        context_chunks: List[RetrievedChunk]
    ) -> tuple[List[VerificationStep], float]:
        """
        Perform Chain-of-Verification checks
        
        Args:
            query: Original query
            answer: Generated answer
            context_chunks: Retrieved context
            
        Returns:
            Tuple of (verification_steps, overall_confidence)
        """
        if not self.enabled:
            return [], 1.0
        
        steps = []
        
        # Step 1: Check if query is answerable from context
        step1 = await self._check_answerability(query, context_chunks)
        steps.append(step1)
        
        # Step 2: Check factual grounding (answer supported by context)
        step2 = await self._check_factual_grounding(answer, context_chunks)
        steps.append(step2)
        
        # Step 3: Check for hallucination indicators
        step3 = await self._check_hallucination_indicators(answer)
        steps.append(step3)
        
        # Compute overall confidence
        overall_confidence = sum(step.confidence for step in steps) / len(steps)
        
        return steps, overall_confidence
    
    async def _check_answerability(
        self,
        query: str,
        context_chunks: List[RetrievedChunk]
    ) -> VerificationStep:
        """Check if query can be answered from context"""
        # Simple heuristic: Check if retrieval found high-quality chunks
        if not context_chunks:
            return VerificationStep(
                step="Answerability Check",
                passed=False,
                confidence=0.0,
                details="No relevant context found"
            )
        
        # Check top chunk similarity score
        top_score = context_chunks[0].score
        
        if top_score >= 0.7:
            passed = True
            confidence = top_score
            details = f"High relevance context found (score: {top_score:.2f})"
        elif top_score >= 0.5:
            passed = True
            confidence = top_score
            details = f"Moderate relevance context found (score: {top_score:.2f})"
        else:
            passed = False
            confidence = top_score
            details = f"Low relevance context (score: {top_score:.2f})"
        
        return VerificationStep(
            step="Answerability Check",
            passed=passed,
            confidence=confidence,
            details=details
        )
    
    async def _check_factual_grounding(
        self,
        answer: str,
        context_chunks: List[RetrievedChunk]
    ) -> VerificationStep:
        """Check if answer is grounded in context"""
        # Extract key claims from answer (simple sentence splitting)
        answer_sentences = [s.strip() for s in answer.split('.') if s.strip()]
        
        if not answer_sentences:
            return VerificationStep(
                step="Factual Grounding",
                passed=True,
                confidence=1.0,
                details="No claims to verify"
            )
        
        # Check if answer contains citations [1], [2], etc.
        citations = re.findall(r'\[\d+\]', answer)
        has_citations = len(citations) > 0
        
        # Combine context text
        context_text = " ".join([chunk.text.lower() for chunk in context_chunks])
        
        # Check overlap between answer and context (simple word matching)
        answer_words = set(answer.lower().split())
        context_words = set(context_text.split())
        overlap = len(answer_words & context_words) / len(answer_words) if answer_words else 0
        
        # Confidence based on citations and overlap
        confidence = (
            (0.5 if has_citations else 0.0) +
            (0.5 * overlap)
        )
        
        passed = confidence >= 0.5
        
        details = f"Citations: {len(citations)}, Context overlap: {overlap:.2%}"
        
        return VerificationStep(
            step="Factual Grounding",
            passed=passed,
            confidence=confidence,
            details=details
        )
    
    async def _check_hallucination_indicators(
        self,
        answer: str
    ) -> VerificationStep:
        """Check for common hallucination patterns"""
        # Common hedging phrases (good signs)
        hedging_phrases = [
            "according to",
            "based on",
            "the document states",
            "as mentioned",
            "i don't have enough information"
        ]
        
        # Hallucination indicators (bad signs)
        hallucination_phrases = [
            "in my opinion",
            "i believe",
            "generally speaking",
            "it is well known",
            "everyone knows"
        ]
        
        answer_lower = answer.lower()
        
        # Count hedging (good)
        hedging_count = sum(1 for phrase in hedging_phrases if phrase in answer_lower)
        
        # Count hallucination indicators (bad)
        hallucination_count = sum(1 for phrase in hallucination_phrases if phrase in answer_lower)
        
        # Check for "I don't know" type responses (good)
        uncertainty_response = any(phrase in answer_lower for phrase in [
            "don't have enough information",
            "cannot answer",
            "not mentioned",
            "unclear from the context"
        ])
        
        if uncertainty_response:
            return VerificationStep(
                step="Hallucination Check",
                passed=True,
                confidence=1.0,
                details="Model appropriately indicated uncertainty"
            )
        
        if hallucination_count > 0:
            confidence = max(0.3, 1.0 - (hallucination_count * 0.2))
            return VerificationStep(
                step="Hallucination Check",
                passed=False,
                confidence=confidence,
                details=f"Detected {hallucination_count} hallucination indicators"
            )
        
        if hedging_count > 0:
            confidence = min(1.0, 0.7 + (hedging_count * 0.1))
            return VerificationStep(
                step="Hallucination Check",
                passed=True,
                confidence=confidence,
                details=f"Found {hedging_count} proper attribution phrases"
            )
        
        # Neutral case
        return VerificationStep(
            step="Hallucination Check",
            passed=True,
            confidence=0.7,
            details="No strong indicators detected"
        )


# Global singleton
_verification_service = None

def get_verification_service() -> VerificationService:
    """Get or create global verification service instance"""
    global _verification_service
    if _verification_service is None:
        _verification_service = VerificationService()
    return _verification_service
