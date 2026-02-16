"""
Integration Tests for Rate Limiting + Quota Tracking
Tests the complete flow without external dependencies
"""
import pytest
from fastapi import HTTPException

from app.middleware.rate_limit import GlobalRateLimiter, get_global_rate_limiter
from app.middleware.quota_tracker import QuotaTracker, get_quota_tracker


class TestIntegrationFlow:
    """Test complete rate limiting + quota tracking flow"""

    def test_singleton_pattern(self):
        """Should return same instance (singleton pattern)"""
        limiter1 = get_global_rate_limiter()
        limiter2 = get_global_rate_limiter()
        assert limiter1 is limiter2

        tracker1 = get_quota_tracker()
        tracker2 = get_quota_tracker()
        assert tracker1 is tracker2

    def test_complete_api_call_simulation(self):
        """Simulate complete API call with rate limit + quota tracking"""
        limiter = get_global_rate_limiter()
        tracker = get_quota_tracker()

        # Simulate embedding API call
        def simulate_voyage_embed(texts):
            # Check rate limit
            if not limiter.check_and_increment("voyage_embeddings"):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            # Simulate API call
            embeddings = [[0.1] * 1024 for _ in texts]

            # Track quota
            estimated_tokens = sum(len(text.split()) * 1.3 for text in texts)
            tracker.record_voyage_usage(int(estimated_tokens))

            return embeddings

        # Test successful calls
        result = simulate_voyage_embed(["test document"])
        assert len(result) == 1

        # Verify quota was tracked
        usage = tracker.get_usage_summary()
        assert usage["voyage_ai"]["tokens_used"] > 0

    def test_rate_limit_protection(self):
        """Should protect against excessive API calls"""
        limiter = GlobalRateLimiter()

        # Simulate spam attack
        successful_calls = 0
        failed_calls = 0

        for i in range(150):
            if limiter.check_and_increment("qdrant_writes"):
                successful_calls += 1
            else:
                failed_calls += 1

        # Should allow up to limit (100), then block
        assert successful_calls == 100
        assert failed_calls == 50

    def test_dashboard_data_accuracy(self):
        """Dashboard should show accurate real-time data"""
        limiter = get_global_rate_limiter()
        tracker = get_quota_tracker()

        # Make some API calls
        for _ in range(10):
            limiter.check_and_increment("groq_queries")
            tracker.record_groq_tokens(500)

        # Get dashboard data
        rate_stats = limiter.get_stats()
        quota_usage = tracker.get_usage_summary()

        # Verify accuracy
        assert rate_stats["groq_queries"]["calls"] == 10
        assert quota_usage["groq"]["tokens_used_lifetime"] >= 5000

    def test_multi_resource_tracking(self):
        """Should track multiple resources independently"""
        # Create new instance to avoid shared state
        limiter = GlobalRateLimiter()

        # Use different resources
        limiter.check_and_increment("voyage_embeddings")
        limiter.check_and_increment("qdrant_writes")
        limiter.check_and_increment("groq_queries")

        stats = limiter.get_stats()

        # Each should have 1 call
        assert stats["voyage_embeddings"]["calls"] == 1
        assert stats["qdrant_writes"]["calls"] == 1
        assert stats["groq_queries"]["calls"] == 1


class TestErrorHandling:
    """Test error scenarios"""

    def test_rate_limit_error_message(self):
        """Should provide clear error message when rate limited"""
        limiter = GlobalRateLimiter()

        # Exhaust limit
        for _ in range(100):
            limiter.check_and_increment("qdrant_writes")

        # Next call should be blocked
        try:
            if not limiter.check_and_increment("qdrant_writes"):
                raise HTTPException(
                    status_code=429,
                    detail="Qdrant write rate limit exceeded. Try again in 1 hour."
                )
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 429
            assert "rate limit exceeded" in e.detail.lower()

    def test_quota_file_corruption_recovery(self):
        """Should handle corrupted quota file gracefully"""
        from pathlib import Path

        # Write corrupted JSON
        QuotaTracker.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        QuotaTracker.DATA_FILE.write_text("invalid json{{{")

        # Should recover and create new tracker
        tracker = QuotaTracker()
        assert tracker._data["voyage_tokens"] == 0

        # Clean up
        QuotaTracker.DATA_FILE.unlink(missing_ok=True)
