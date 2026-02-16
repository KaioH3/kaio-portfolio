"""
Tests for Rate Limiting and Quota Tracking
"""
import pytest
import time
from pathlib import Path

from app.middleware.rate_limit import GlobalRateLimiter
from app.middleware.quota_tracker import QuotaTracker


class TestGlobalRateLimiter:
    """Test global rate limiter for API protection"""

    def test_allows_within_limit(self):
        """Should allow calls within the hourly limit"""
        limiter = GlobalRateLimiter()

        # Should allow up to 1000 calls for voyage_embeddings
        for i in range(100):
            assert limiter.check_and_increment("voyage_embeddings") is True

    def test_blocks_after_limit(self):
        """Should block calls after exceeding hourly limit"""
        limiter = GlobalRateLimiter()

        # Exhaust the limit (100 for qdrant_writes for faster test)
        for i in range(100):
            limiter.check_and_increment("qdrant_writes")

        # Next call should fail
        assert limiter.check_and_increment("qdrant_writes") is False

    def test_reset_after_hour(self):
        """Should reset counter after 1 hour"""
        limiter = GlobalRateLimiter()

        # Manually set reset time to past
        limiter._limits["groq_queries"]["reset"] = time.time() - 1
        limiter._limits["groq_queries"]["calls"] = 999

        # Should reset and allow new call
        assert limiter.check_and_increment("groq_queries") is True
        assert limiter._limits["groq_queries"]["calls"] == 1

    def test_get_stats(self):
        """Should return accurate statistics"""
        limiter = GlobalRateLimiter()

        # Make some calls
        for i in range(10):
            limiter.check_and_increment("voyage_embeddings")

        stats = limiter.get_stats()

        assert "voyage_embeddings" in stats
        assert stats["voyage_embeddings"]["calls"] == 10
        assert stats["voyage_embeddings"]["max"] == 1000
        assert "reset_in" in stats["voyage_embeddings"]

    def test_thread_safety(self):
        """Should be thread-safe"""
        import threading

        limiter = GlobalRateLimiter()
        results = []

        def make_calls():
            for _ in range(10):
                results.append(limiter.check_and_increment("groq_queries"))

        threads = [threading.Thread(target=make_calls) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All 50 calls should succeed (within limit)
        assert sum(results) == 50


class TestQuotaTracker:
    """Test quota tracking for cumulative usage"""

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up test data file after each test"""
        yield
        test_file = Path("./data/quota_usage.json")
        if test_file.exists():
            # Reset to zero for next test
            tracker = QuotaTracker()
            tracker._data = {
                "voyage_tokens": 0,
                "qdrant_documents": 0,
                "groq_tokens": 0,
            }
            tracker._save()

    def test_record_voyage_usage(self):
        """Should record Voyage AI token usage"""
        tracker = QuotaTracker()

        tracker.record_voyage_usage(1000)
        summary = tracker.get_usage_summary()

        assert summary["voyage_ai"]["tokens_used"] >= 1000

    def test_record_qdrant_documents(self):
        """Should record Qdrant document count"""
        tracker = QuotaTracker()

        tracker.record_qdrant_documents(50)
        summary = tracker.get_usage_summary()

        assert summary["qdrant"]["documents"] >= 50

    def test_record_groq_tokens(self):
        """Should record Groq token usage"""
        tracker = QuotaTracker()

        tracker.record_groq_tokens(2000)
        summary = tracker.get_usage_summary()

        assert summary["groq"]["tokens_used_lifetime"] >= 2000

    def test_persistence(self):
        """Should persist data across instances"""
        tracker1 = QuotaTracker()
        tracker1.record_voyage_usage(5000)

        # Create new instance (simulates app restart)
        tracker2 = QuotaTracker()
        summary = tracker2.get_usage_summary()

        # Data should persist
        assert summary["voyage_ai"]["tokens_used"] >= 5000

    def test_percentage_calculation(self):
        """Should calculate usage percentage correctly"""
        tracker = QuotaTracker()

        tracker.record_voyage_usage(2_000_000)  # 2M tokens
        summary = tracker.get_usage_summary()

        # 2M / 200M = 1%
        expected_percentage = (2_000_000 / 200_000_000) * 100
        assert summary["voyage_ai"]["percentage"] >= expected_percentage

    def test_thread_safety(self):
        """Should be thread-safe"""
        import threading

        tracker = QuotaTracker()

        def record_usage():
            for _ in range(10):
                tracker.record_voyage_usage(100)

        threads = [threading.Thread(target=record_usage) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        summary = tracker.get_usage_summary()
        # 5 threads * 10 calls * 100 tokens = 5000 tokens
        assert summary["voyage_ai"]["tokens_used"] >= 5000
