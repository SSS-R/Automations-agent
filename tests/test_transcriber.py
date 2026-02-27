"""Tests for app.services.transcriber utility functions."""
import sys
from pathlib import Path

# Add project root to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.transcriber import format_timestamp, format_for_llm, parse_vtt_file, parse_srt_file, _parse_vtt_timestamp, parse_subtitle_file


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


class TestParseVttTimestamp:
    def test_basic(self):
        assert _parse_vtt_timestamp("00:00:01.234") == 1.234

    def test_minutes(self):
        assert _parse_vtt_timestamp("00:01:30.000") == 90.0

    def test_hours(self):
        assert _parse_vtt_timestamp("01:00:00.000") == 3600.0


class TestParseVttFile:
    def test_basic_vtt(self, tmp_path):
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:05.000
Hello world this is a test

00:00:05.500 --> 00:00:10.000
Another line of subtitles
"""
        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text(vtt_content, encoding='utf-8')

        segments = parse_vtt_file(str(vtt_file))
        assert len(segments) == 2
        assert segments[0]["text"] == "Hello world this is a test"
        assert segments[0]["start"] == 1.0
        assert segments[0]["end"] == 5.0
        assert segments[0]["words"] == []

    def test_strips_vtt_tags(self, tmp_path):
        vtt_content = """WEBVTT

00:00:01.000 --> 00:00:05.000
<c>Hello</c> <c>world</c>
"""
        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text(vtt_content, encoding='utf-8')

        segments = parse_vtt_file(str(vtt_file))
        assert "Hello" in segments[0]["text"]
        assert "<c>" not in segments[0]["text"]


class TestParseSrtFile:
    def test_basic_srt(self, tmp_path):
        srt_content = """1
00:00:01,000 --> 00:00:05,000
Hello world

2
00:00:05,500 --> 00:00:10,000
Another subtitle
"""
        srt_file = tmp_path / "test.srt"
        srt_file.write_text(srt_content, encoding='utf-8')

        segments = parse_srt_file(str(srt_file))
        assert len(segments) == 2
        assert segments[0]["text"] == "Hello world"
        assert segments[0]["start"] == 1.0
        assert segments[1]["text"] == "Another subtitle"


class TestParseSubtitleFile:
    def test_dispatches_vtt(self, tmp_path):
        vtt_file = tmp_path / "test.vtt"
        vtt_file.write_text("WEBVTT\n\n00:00:01.000 --> 00:00:05.000\nHello\n", encoding='utf-8')
        result = parse_subtitle_file(str(vtt_file))
        assert result is not None
        assert len(result) == 1

    def test_dispatches_srt(self, tmp_path):
        srt_file = tmp_path / "test.srt"
        srt_file.write_text("1\n00:00:01,000 --> 00:00:05,000\nHello\n", encoding='utf-8')
        result = parse_subtitle_file(str(srt_file))
        assert result is not None

    def test_returns_none_for_unknown(self):
        result = parse_subtitle_file("test.txt")
        assert result is None
