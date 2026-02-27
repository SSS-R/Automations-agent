import pytest


@pytest.fixture
def sample_segments():
    """Sample transcript segments with word-level timestamps from faster-whisper."""
    return [
        {
            "start": 10.5,
            "end": 15.2,
            "text": "Welcome back everyone to the show",
            "words": [
                {"word": "Welcome", "start": 10.5, "end": 10.9, "probability": 0.95},
                {"word": "back", "start": 10.9, "end": 11.2, "probability": 0.98},
                {"word": "everyone", "start": 11.2, "end": 11.8, "probability": 0.92},
                {"word": "to", "start": 11.8, "end": 12.0, "probability": 0.99},
                {"word": "the", "start": 12.0, "end": 12.1, "probability": 0.99},
                {"word": "show", "start": 12.1, "end": 12.5, "probability": 0.97},
            ]
        },
        {
            "start": 15.2,
            "end": 20.0,
            "text": "Today we are going to talk about AI",
            "words": [
                {"word": "Today", "start": 15.2, "end": 15.6, "probability": 0.96},
                {"word": "we", "start": 15.6, "end": 15.8, "probability": 0.99},
                {"word": "are", "start": 15.8, "end": 16.0, "probability": 0.98},
                {"word": "going", "start": 16.0, "end": 16.3, "probability": 0.97},
                {"word": "to", "start": 16.3, "end": 16.5, "probability": 0.99},
                {"word": "talk", "start": 16.5, "end": 16.8, "probability": 0.95},
                {"word": "about", "start": 16.8, "end": 17.1, "probability": 0.96},
                {"word": "AI", "start": 17.1, "end": 17.5, "probability": 0.94},
            ]
        },
    ]


@pytest.fixture
def sample_segments_no_words():
    """Segments without word-level timestamps (fallback testing)."""
    return [
        {
            "start": 5.0,
            "end": 10.0,
            "text": "This is a test segment",
        },
        {
            "start": 10.0,
            "end": 14.0,
            "text": "Another segment here",
        },
    ]


@pytest.fixture
def sample_highlights():
    """Sample highlight detection results."""
    return [
        {
            "start": "00:02:10",
            "end": "00:02:45",
            "hook": "You won't believe what happened next",
            "reason": "Strong emotional hook",
            "viral_score": 9
        },
        {
            "start": "00:05:30",
            "end": "00:06:15",
            "hook": "This changed everything",
            "reason": "Surprising revelation",
            "viral_score": 7
        },
    ]
