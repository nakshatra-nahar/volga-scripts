from pathlib import Path

from fastapi.testclient import TestClient

from app import app

SAMPLES = Path(__file__).parent.parent / "samples"
client = TestClient(app)


def test_returns_ordered_segments_with_timestamps():
    for name in ["hello.wav", "hello.mp3"]:
        r = client.post("/transcribe", files={"file": (name, (SAMPLES / name).read_bytes())})
        assert r.status_code == 200, r.text
        segments = r.json()["segments"]
        # The sample has a 1.5 s pause between two sentences.
        assert len(segments) >= 2
        assert "second sentence" in segments[-1]["text"].lower()
        prev_end = 0
        for s in segments:
            assert prev_end <= s["start"] < s["end"] <= 6.92  # sample is 6.91 s long
            prev_end = s["end"]


def test_rejects_non_audio():
    r = client.post("/transcribe", files={"file": ("fake.mp3", b"not audio" * 100)})
    assert r.status_code == 400
