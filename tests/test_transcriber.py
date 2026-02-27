"""Tests for app.services.transcriber utility functions."""
import sys
from pathlib import Path

# Add project root to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.transcriber import format_timestamp, format_for_llm


class TestFormatTimestamp:
    def test_zero_seconds(self):
        assert format_timestamp(0) == "00:00:00"

    def test_seconds_only(self):
        assert format_timestamp(45) == "00:00:45"

    def test_minutes_and_seconds(self):
        assert format_timestamp(65) == "00:01:05"

    def test_hours_minutes_seconds(self):
        assert format_timestamp(3661) == "01:01:01"

    def test_large_value(self):
        assert format_timestamp(7200) == "02:00:00"

    def test_fractional_seconds_truncated(self):
        # format_timestamp truncates to int seconds
        assert format_timestamp(10.7) == "00:00:10"


class TestFormatForLlm:
    def test_basic_formatting(self, sample_segments):
        result = format_for_llm(sample_segments)
        lines = result.strip().split("\n")
        assert len(lines) == 2
        assert "[00:00:10 → 00:00:15]" in lines[0]
        assert "Welcome back everyone" in lines[0]

    def test_empty_segments(self):
        result = format_for_llm([])
        assert result == ""

    def test_single_segment(self):
        segments = [{"start": 0.0, "end": 5.0, "text": "Hello world"}]
        result = format_for_llm(segments)
        assert "[00:00:00 → 00:00:05] Hello world" == result
