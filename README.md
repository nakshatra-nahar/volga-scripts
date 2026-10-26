# volga-scripts

Three small speech-to-text services. Each folder is self-contained and has its own `app.py`, `requirements.txt`, tests and README.

| Folder | Task | Endpoint |
|---|---|---|
| [`01-audio-input`](01-audio-input) | Accept an audio file (WAV or MP3) | `POST /upload` |
| [`02-transcription`](02-transcription) | Transcribe spoken language into text | `POST /transcribe` → `{"text"}` |
| [`03-timestamped-transcription`](03-timestamped-transcription) | Return the transcription with timestamps per segment | `POST /transcribe` → `{"text", "segments"}` |

`samples/` contains a short spoken WAV and MP3 that the tests use.

## Quick start (Python 3.10+)

```bash
cd 03-timestamped-transcription
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --port 8003
curl -F file=@../samples/hello.mp3 localhost:8003/transcribe
```

Interactive API docs are served at `http://localhost:<port>/docs`.
