"""
Tests for the UsageTracker: record, get_count, get_usage.
Uses a temp SQLite DB for isolation.
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone

import pytest

from api.usage import UsageTracker


@pytest.fixture
def tracker():
    """Create a UsageTracker with a temporary database."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    t = UsageTracker(db_path=path)
    yield t
    os.unlink(path)


class TestUsageTracker:
    def test_record_and_count(self, tracker):
        tracker.record("key-abc")
        tracker.record("key-abc")
        tracker.record("key-abc")
        assert tracker.get_count("key-abc") == 3

    def test_count_zero_for_unknown_key(self, tracker):
        assert tracker.get_count("nonexistent-key") == 0

    def test_separate_keys_tracked_independently(self, tracker):
        tracker.record("key-1")
        tracker.record("key-1")
        tracker.record("key-2")
        assert tracker.get_count("key-1") == 2
        assert tracker.get_count("key-2") == 1

    def test_five_records_equals_five(self, tracker):
        """Plan requirement: 'After 5 successful chart creations with key X, stored count for X is 5'."""
        for _ in range(5):
            tracker.record("key-X")
        assert tracker.get_count("key-X") == 5

    def test_count_by_specific_period(self, tracker):
        current_period = datetime.now(timezone.utc).strftime("%Y-%m")
        tracker.record("key-a")
        tracker.record("key-a")

        assert tracker.get_count("key-a", period=current_period) == 2
        assert tracker.get_count("key-a", period="1999-01") == 0  # Different period

    def test_get_usage_returns_dict(self, tracker):
        tracker.record("key-abc-12345678")
        tracker.record("key-abc-12345678")

        usage = tracker.get_usage("key-abc-12345678")
        assert isinstance(usage, dict)
        assert usage["api_key"] == "key-abc-..."  # Masked
        assert usage["request_count"] == 2
        assert "period_start" in usage

    def test_get_usage_masks_key(self, tracker):
        usage = tracker.get_usage("super-secret-long-api-key")
        assert "super-se..." == usage["api_key"]
        assert "super-secret" not in usage["api_key"]

    def test_record_with_custom_endpoint(self, tracker):
        tracker.record("key-1", endpoint="/v1/custom")
        assert tracker.get_count("key-1") == 1

    def test_db_persists_across_instances(self):
        """Verify data persists in SQLite across UsageTracker instances."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            t1 = UsageTracker(db_path=path)
            t1.record("persistent-key")
            t1.record("persistent-key")

            # New instance, same DB
            t2 = UsageTracker(db_path=path)
            assert t2.get_count("persistent-key") == 2
        finally:
            os.unlink(path)
