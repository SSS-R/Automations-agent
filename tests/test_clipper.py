"""Tests for app.services.clipper utility functions."""
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.clipper import format_time, generate_srt, generate_captions_json


class TestFormatTime:
    def test_zero(self):
        assert format_time(0) == "00:00:00.000"

    def test_seconds(self):
        assert format_time(30.5) == "00:00:30.500"

    def test_minutes(self):
        assert format_time(90.25) == "00:01:30.250"

    def test_hours(self):
        result = format_time(3661.123)
        assert result == "01:01:01.123"

    def test_precision(self):
        result = format_time(1.1)
        assert result == "00:00:01.100"


class TestGenerateSrt:
    def test_basic_srt_output(self, sample_segments, tmp_path):
        output = str(tmp_path / "test.srt")
        generate_srt(sample_segments, output, offset=10.0)

        content = Path(output).read_text(encoding='utf-8')
        # First subtitle should start at ~0.5s (10.5 - 10.0 offset)
        assert "1\n" in content
        assert "Welcome back everyone to the show" in content

    def test_offset_clips_early_segments(self, tmp_path):
        segments = [
            {"start": 2.0, "end": 5.0, "text": "Skipped"},
            {"start": 10.0, "end": 15.0, "text": "Included"},
        ]
        output = str(tmp_path / "test.srt")
        generate_srt(segments, output, offset=8.0)

        content = Path(output).read_text(encoding='utf-8')
        # First segment (2.0) - offset (8.0) = -6.0, end is -3.0 → skipped
        assert "Skipped" not in content
        assert "Included" in content

    def test_empty_segments(self, tmp_path):
        output = str(tmp_path / "test.srt")
        generate_srt([], output)
        content = Path(output).read_text(encoding='utf-8')
        assert content == ""


class TestGenerateCaptionsJson:
    def test_uses_word_timestamps(self, sample_segments, tmp_path):
        """When segments have word-level timestamps, those should be used."""
        output = str(tmp_path / "captions.json")
        generate_captions_json(sample_segments, output, offset=10.0)

        data = json.loads(Path(output).read_text())
        # First word "Welcome" starts at 10.5, offset 10.0 → 500ms
        assert data[0]["text"] == "Welcome "
        assert data[0]["startMs"] == 500
        assert data[0]["endMs"] == 900  # 10.9 - 10.0 = 0.9s = 900ms

    def test_fallback_linear_estimation(self, sample_segments_no_words, tmp_path):
        """When segments lack word timestamps, fall back to linear estimation."""
        output = str(tmp_path / "captions.json")
        generate_captions_json(sample_segments_no_words, output, offset=0.0)

        data = json.loads(Path(output).read_text())
        # "This is a test segment" → 5 words over 5s (5000ms)
        assert len(data) > 0
        assert data[0]["text"] == "This "
        assert data[0]["startMs"] == 5000  # segment starts at 5.0s

    def test_empty_segments(self, tmp_path):
        output = str(tmp_path / "captions.json")
        generate_captions_json([], output)
        data = json.loads(Path(output).read_text())
        assert data == []

    def test_word_count_matches(self, sample_segments, tmp_path):
        """Total caption entries should match total words across all segments."""
        output = str(tmp_path / "captions.json")
        generate_captions_json(sample_segments, output, offset=0.0)

        data = json.loads(Path(output).read_text())
        total_words = sum(len(s['words']) for s in sample_segments)
        assert len(data) == total_words
