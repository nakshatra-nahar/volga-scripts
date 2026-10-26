"""Service that transcribes spoken language in an uploaded audio file into text."""
import os

import av
from fastapi import FastAPI, HTTPException, UploadFile
from faster_whisper import WhisperModel

model = WhisperModel(os.getenv("WHISPER_MODEL", "base"), device="cpu", compute_type="int8")
app = FastAPI(title="Transcription")


@app.post("/transcribe")
def transcribe(file: UploadFile):
    try:
        segments, _ = model.transcribe(file.file, beam_size=5)
        text = "".join(s.text for s in segments).strip()  # segments is lazy; decoding happens here
    except av.error.FFmpegError:
        raise HTTPException(400, "File is not decodable audio")
    return {"text": text}
