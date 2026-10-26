# 03 · Timestamped transcription

A service that transcribes an uploaded audio file and returns timestamps (in seconds) for each segment. It uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) on the CPU.

- `POST /transcribe` (multipart field `file`) → `{"text", "segments": [{"start", "end", "text"}]}`
- Segments are in order and don't overlap. Each `end` is capped at the audio's length, because Whisper can predict an end time past it.
- Returns 400 if the file can't be decoded as audio. Set the model with `WHISPER_MODEL` (default `base`).

```bash
pip install -r requirements.txt
uvicorn app:app --port 8003
curl -F file=@../samples/hello.wav localhost:8003/transcribe
```

```json
{
  "text": "Hello world, this is a test of the transcription service. The second sentence comes after a short pause.",
  "segments": [
    {"start": 0.0, "end": 4.64, "text": "Hello world, this is a test of the transcription service."},
    {"start": 4.64, "end": 6.91, "text": "The second sentence comes after a short pause."}
  ]
}
```

```bash
pytest
```
