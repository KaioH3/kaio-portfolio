"""
Rate Limiter - IP-based monthly query limit
Persists to JSON file to survive restarts
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Tuple

from ..config import rag_config

logger = logging.getLogger(__name__)

DATA_FILE = Path(rag_config.QDRANT_PATH).parent / "rate_limits.json"


class RateLimiter:
    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        try:
            if DATA_FILE.exists():
                return json.loads(DATA_FILE.read_text())
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Rate limit data corrupted, resetting: {e}")
        return {}

    def _save(self) -> None:
        try:
            DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            DATA_FILE.write_text(json.dumps(self._data))
        except OSError as e:
            logger.error(f"Failed to save rate limit data: {e}")

    def check(self, ip: str) -> Tuple[bool, int]:
        """Check if IP can make a query. Returns (allowed, remaining)."""
        month_key = datetime.utcnow().strftime("%Y-%m")
        limit = rag_config.RATE_LIMIT_MONTHLY

        # Clean old months
        if ip in self._data:
            self._data[ip] = {
                k: v for k, v in self._data[ip].items() if k == month_key
            }

        count = self._data.get(ip, {}).get(month_key, 0)
        remaining = max(0, limit - count)
        return count < limit, remaining

    def increment(self, ip: str) -> int:
        """Record a query for this IP. Returns remaining queries."""
        month_key = datetime.utcnow().strftime("%Y-%m")
        limit = rag_config.RATE_LIMIT_MONTHLY

        if ip not in self._data:
            self._data[ip] = {}
        self._data[ip][month_key] = self._data[ip].get(month_key, 0) + 1
        self._save()

        return max(0, limit - self._data[ip][month_key])


_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
