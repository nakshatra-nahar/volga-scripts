from pathlib import Path

from fastapi.testclient import TestClient

from app import app

SAMPLES = Path(__file__).parent.parent / "samples"
client = TestClient(app)


def test_transcribes_wav_and_mp3():
    for name in ["hello.wav", "hello.mp3"]:
        r = client.post("/transcribe", files={"file": (name, (SAMPLES / name).read_bytes())})
        assert r.status_code == 200, r.text
        text = r.json()["text"].lower()
        assert "transcription service" in text and "second sentence" in text


def test_rejects_non_audio():
    r = client.post("/transcribe", files={"file": ("fake.wav", b"not audio" * 100)})
    assert r.status_code == 400
