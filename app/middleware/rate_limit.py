"""
Global Rate Limiter - API Protection Layer
Protects external APIs (Voyage AI, Qdrant, Groq) against abuse
"""
import time
from threading import Lock
from typing import Dict, Literal

ResourceType = Literal["voyage_embeddings", "qdrant_writes", "groq_queries"]


class GlobalRateLimiter:
    """
    Rate limiter para proteger APIs externas contra abuse.

    Limites por hora (reset automático):
    - Voyage AI: 1000 embeddings/hora (evita esgotar 200M tokens)
    - Qdrant: 100 writes/hora (evita spam de indexação)
    - Groq: 500 queries/hora (respeita free tier)
    """

    def __init__(self):
        self._limits: Dict[ResourceType, Dict] = {
            "voyage_embeddings": {"calls": 0, "reset": 0, "max": 1000},
            "qdrant_writes": {"calls": 0, "reset": 0, "max": 100},
            "groq_queries": {"calls": 0, "reset": 0, "max": 500},
        }
        self._lock = Lock()

    def check_and_increment(self, resource: ResourceType) -> bool:
        """
        Verifica se recurso está dentro do limite e incrementa contador.
        Retorna True se permitido, False se excedeu limite.
        """
        with self._lock:
            now = time.time()
            limit = self._limits[resource]

            # Reset a cada hora
            if now > limit["reset"]:
                limit["calls"] = 0
                limit["reset"] = now + 3600  # +1 hour

            # Check limite
            if limit["calls"] >= limit["max"]:
                return False

            limit["calls"] += 1
            return True

    def get_stats(self) -> Dict:
        """Retorna estatísticas de uso atuais (para dashboard)"""
        with self._lock:
            return {
                resource: {
                    "calls": limit["calls"],
                    "max": limit["max"],
                    "reset_in": max(0, int(limit["reset"] - time.time())),
                }
                for resource, limit in self._limits.items()
            }


# Singleton
_global_limiter = None


def get_global_rate_limiter() -> GlobalRateLimiter:
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = GlobalRateLimiter()
    return _global_limiter
