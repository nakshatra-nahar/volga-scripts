"""Service that accepts a WAV or MP3 upload, validates it, and stores it on disk."""
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile

UPLOAD_DIR = Path(__file__).parent / "uploads"
MAX_BYTES = 25 * 1024 * 1024

app = FastAPI(title="Audio input")


def detect_format(head: bytes) -> str | None:
    # Sniff content, not the filename: a renamed .txt must not pass as audio.
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "wav"
    # ID3 tag, or a bare MPEG Layer III frame header (11 sync bits + layer bits 01).
    if head[:3] == b"ID3" or (len(head) > 1 and head[0] == 0xFF and head[1] & 0xE6 == 0xE2):
        return "mp3"
    return None


@app.post("/upload")
def upload(file: UploadFile):
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "File larger than 25 MB")
    fmt = detect_format(data)
    if fmt is None:
        raise HTTPException(415, "Only WAV or MP3 audio is accepted")
    UPLOAD_DIR.mkdir(exist_ok=True)
    file_id = uuid.uuid4().hex
    (UPLOAD_DIR / f"{file_id}.{fmt}").write_bytes(data)
    return {"id": file_id, "filename": file.filename, "format": fmt, "size_bytes": len(data)}
