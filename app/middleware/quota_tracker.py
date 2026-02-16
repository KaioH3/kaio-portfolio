"""
Quota Tracker - Cumulative Usage Monitoring
Tracks lifetime usage of external API quotas
"""
import json
from pathlib import Path
from typing import Dict
from threading import Lock


class QuotaTracker:
    """
    Rastreia uso cumulativo de quotas das APIs externas.
    Persiste em JSON para sobreviver restarts.
    """

    DATA_FILE = Path("./data/quota_usage.json")

    def __init__(self):
        self._data = self._load()
        self._lock = Lock()

    def _load(self) -> Dict:
        try:
            if self.DATA_FILE.exists():
                return json.loads(self.DATA_FILE.read_text())
        except Exception:
            pass
        return {
            "voyage_tokens": 0,  # Total tokens usados
            "qdrant_documents": 0,  # Total documentos indexados
            "groq_tokens": 0,  # Total tokens LLM usados
        }

    def _save(self):
        try:
            self.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            self.DATA_FILE.write_text(json.dumps(self._data, indent=2))
        except Exception as e:
            print(f"Failed to save quota data: {e}")

    def record_voyage_usage(self, num_tokens: int):
        """Registra uso de tokens Voyage AI"""
        with self._lock:
            self._data["voyage_tokens"] += num_tokens
            self._save()

    def record_qdrant_documents(self, num_docs: int):
        """Registra documentos adicionados ao Qdrant"""
        with self._lock:
            self._data["qdrant_documents"] += num_docs
            self._save()

    def record_groq_tokens(self, num_tokens: int):
        """Registra tokens usados no Groq"""
        with self._lock:
            self._data["groq_tokens"] += num_tokens
            self._save()

    def get_usage_summary(self) -> Dict:
        """Retorna resumo de uso para dashboard"""
        with self._lock:
            return {
                "voyage_ai": {
                    "tokens_used": self._data["voyage_tokens"],
                    "tokens_limit": 200_000_000,  # 200M one-time
                    "percentage": (self._data["voyage_tokens"] / 200_000_000) * 100,
                },
                "qdrant": {
                    "documents": self._data["qdrant_documents"],
                    "storage_mb": (self._data["qdrant_documents"] * 2.5) / 1024,
                    "limit_gb": 1.0,
                    "percentage": ((self._data["qdrant_documents"] * 2.5 / 1024) / 1024) * 100,
                },
                "groq": {
                    "tokens_used_lifetime": self._data["groq_tokens"],
                    "daily_limit": 100_000,  # Resets daily
                },
            }


# Singleton
_quota_tracker = None


def get_quota_tracker() -> QuotaTracker:
    global _quota_tracker
    if _quota_tracker is None:
        _quota_tracker = QuotaTracker()
    return _quota_tracker
