"""Tests for app.services.highlighter utility functions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.highlighter import timestamp_to_seconds


class TestTimestampToSeconds:
    def test_hhmmss_format(self):
        assert timestamp_to_seconds("01:30:00") == 5400.0

    def test_hhmmss_with_seconds(self):
        assert timestamp_to_seconds("00:02:10") == 130.0

    def test_mmss_format(self):
        assert timestamp_to_seconds("05:30") == 330.0

    def test_zero(self):
        assert timestamp_to_seconds("00:00:00") == 0.0

    def test_raw_seconds_string(self):
        assert timestamp_to_seconds("45") == 45.0

    def test_mmss_zero(self):
        assert timestamp_to_seconds("00:00") == 0.0

    def test_complex_time(self):
        assert timestamp_to_seconds("02:15:45") == 8145.0
