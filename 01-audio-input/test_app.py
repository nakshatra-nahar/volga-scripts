from pathlib import Path

from fastapi.testclient import TestClient

from app import UPLOAD_DIR, app

SAMPLES = Path(__file__).parent.parent / "samples"
client = TestClient(app)


def post(name, data):
    return client.post("/upload", files={"file": (name, data)})


def test_accepts_wav_and_mp3():
    for name, fmt in [("hello.wav", "wav"), ("hello.mp3", "mp3")]:
        data = (SAMPLES / name).read_bytes()
        r = post(name, data)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["format"] == fmt and body["size_bytes"] == len(data)
        assert (UPLOAD_DIR / f"{body['id']}.{fmt}").read_bytes() == data


def test_rejects_non_audio_even_with_audio_extension():
    assert post("fake.wav", b"just some text, not audio").status_code == 415
    assert post("empty.mp3", b"").status_code == 415
