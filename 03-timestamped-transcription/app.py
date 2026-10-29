"""Service that transcribes an uploaded audio file and returns timestamps per segment."""
import os

import av
from fastapi import FastAPI, HTTPException, UploadFile
from faster_whisper import WhisperModel

model = WhisperModel(os.getenv("WHISPER_MODEL", "base"), device="cpu", compute_type="int8")
app = FastAPI(title="Timestamped transcription")


@app.post("/transcribe")
def transcribe(file: UploadFile):
    try:
        segments, info = model.transcribe(file.file, beam_size=5)
        # segments is lazy; the model runs here. Times are seconds from the start of the audio;
        # Whisper can predict a final end past the audio, so clamp it to the real duration.
        segments = [
            {"start": round(s.start, 2), "end": round(min(s.end, info.duration), 2), "text": s.text.strip()}
            for s in segments
        ]
    except av.error.FFmpegError:
        raise HTTPException(400, "File is not decodable audio")
    return {"text": " ".join(s["text"] for s in segments), "segments": segments}
