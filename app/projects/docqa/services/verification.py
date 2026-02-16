"""Chain-of-Verification (simplified for MVP)"""
from typing import List
import logging
from ..models import RetrievedChunk, VerificationStep

logger = logging.getLogger(__name__)


class VerificationService:
    def verify(self, answer: str, chunks: List[RetrievedChunk]) -> List[VerificationStep]:
        steps = []
        # Source coverage check
        has_sources = any(f"[{i}]" in answer for i in range(1, len(chunks) + 1))
        steps.append(VerificationStep(
            step="Source Citation", passed=has_sources,
            confidence=0.9 if has_sources else 0.3,
            details="Answer cites sources" if has_sources else "No source citations found",
        ))
        # Context grounding check
        answer_words = set(answer.lower().split())
        context_words = set()
        for c in chunks:
            context_words.update(c.text.lower().split())
        overlap = len(answer_words & context_words) / max(len(answer_words), 1)
        grounded = overlap > 0.3
        steps.append(VerificationStep(
            step="Context Grounding", passed=grounded,
            confidence=min(overlap * 1.5, 1.0),
            details=f"Word overlap: {overlap:.0%}",
        ))
        return steps


_verification_service = None

def get_verification_service() -> VerificationService:
    global _verification_service
    if _verification_service is None:
        _verification_service = VerificationService()
    return _verification_service
