# volga-scripts: speech-to-text services

Three small HTTP services that together turn an audio file into a transcript with timestamps. Each requirement has its own self-contained folder with its own code, dependencies, tests and README.

| Folder | Requirement | Endpoint |
|---|---|---|
| [`01-audio-input`](01-audio-input) | Accept an audio file (WAV or MP3) | `POST /upload` |
| [`02-transcription`](02-transcription) | Transcribe spoken language into text | `POST /transcribe` → `{"text"}` |
| [`03-timestamped-transcription`](03-time stamped-transcription) | Return the transcription with timestamps per segment | `POST /transcribe` → `{"text", "segments"}` |

## Quick start

Requires Python 3.10+. No GPU, PyTorch or system FFmpeg is needed.  

```bash
cd 03-timestamped-transcription
python -m venv .venv && source .venv/bin/activate
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

The first start downloads the Whisper model (about 145 MB for `base`). Interactive API docs are at `http://localhost:<port>/docs`. To run the tests, run `pytest` inside each folder.

## How it works

1. The client uploads the file as `multipart/form-data`. FastAPI keeps small uploads in memory and writes anything over 1 MB to a temporary file.
2. **01-audio-input** reads at most 25 MB, identifies WAV or MP3 from the file's first bytes, and saves it as `uploads/<uuid>.<wav|mp3>`.
3. **02** and **03** pass the uploaded file object straight to faster-whisper. It decodes the audio with PyAV (which bundles FFmpeg), converts it to 16 kHz mono, detects the language, and runs Whisper over the audio in 30-second windows.
4. faster-whisper returns segments as a lazy generator, so the model runs while the endpoint reads them. **02** joins the text into one string. **03** returns each segment's start and end time in seconds (rounded to 0.01 s) along with its text.

## Design decisions

### One folder per requirement

Each requirement is a separate, self-contained service, so it can be run, tested and reviewed on its own. The cost is a few duplicated lines: 02 and 03 load the model the same way. In production I would merge them into one API (see [Limitations and next steps](#limitations-and-next-steps)).

### FastAPI for the services

An HTTP upload endpoint is the natural way for a client to send an audio file. FastAPI handles multipart uploads, generates OpenAPI docs automatically, and has a test client that exercises the real request path. The endpoints are plain `def` functions rather than `async def`. Transcription is CPU-heavy, and FastAPI runs plain functions in a thread pool, so one long request doesn't block the server.

### faster-whisper as the speech engine

faster-whisper runs OpenAI's open-source Whisper model on CTranslate2, an optimized inference engine. I chose it because:

- It runs well on an ordinary CPU with 8-bit (int8) quantization and needs no GPU or PyTorch. Its authors report it is up to 4x faster than the original Whisper code, with the same accuracy and less memory.
- It returns segments with start and end times built in, which is exactly what requirement 3 asks for.
- It decodes audio itself through PyAV, so common formats work without extra code or a system FFmpeg install.
- It runs locally, so audio never leaves the machine and there is no per-minute API cost.

Alternatives I considered:

- The original `openai-whisper` package: slower on a CPU, and it needs PyTorch.
- whisper.cpp: fast, but it needs compiling and Python bindings.
- Cloud APIs such as OpenAI, Google or AWS: no model to host, but they charge per minute, need a network connection, and send user audio to a third party.

The model is loaded once at startup, not per request. The default size is `base`, a good balance of speed and accuracy on a CPU. Set `WHISPER_MODEL` to `tiny`, `small`, `medium` or `large-v3` to trade speed for accuracy. Transcription uses beam search with a beam size of 5, which is more accurate than greedy decoding.

### Validate uploads by content, not by name

The file extension and the `Content-Type` header both come from the client and are easy to fake. 01-audio-input checks the first bytes of the file instead:

- **WAV:** starts with `RIFF` and has `WAVE` at byte 8.
- **MP3:** starts with an `ID3` tag, or with an MPEG frame header whose 11 sync bits are set and whose layer bits say Layer III.

A text file renamed to `.wav` is rejected with 415, and a file over 25 MB with 413. Saved files are named with a random UUID, never the client's filename, so a crafted filename can't write outside the uploads folder.

### Let the decoder validate input in the transcription services

02 and 03 don't restrict formats: anything FFmpeg can decode (WAV, MP3, M4A/AAC, FLAC, OGG/Opus and more) can be transcribed. Decoding is the validation. If it fails, PyAV raises an `FFmpegError`, and the service returns it as a 400 instead of a 500.

### Cap end timestamps at the audio's length

Whisper sometimes predicts a final end time past the end of the audio. On the test WAV it reported 7.64 s for audio that is 6.91 s long. 03 caps every end time at the real duration that faster-whisper reports.

## Testing

The tests use real speech, not mocks. `samples/` has a 6.9-second clip generated with the macOS `say` command: two sentences with a 1.5-second pause between them, saved as a 16 kHz mono WAV and a 32 kbps MP3. Each folder has two tests that call its service through FastAPI's test client:

| Folder | What the tests check |
|---|---|
| 01 | WAV and MP3 are accepted and saved byte-for-byte. Non-audio content and empty files are rejected, even with an audio extension. |
| 02 | Both samples produce text containing both sentences. Non-audio is rejected with 400. |
| 03 | At least two segments, in order, not overlapping, and none ending after the audio. Non-audio is rejected with 400. |

Testing caught two real problems, and both are fixed:

- **Timestamps past the end of the audio**, described above.
- **A dependency break.** faster-whisper 1.2.1 passes an argument (`metadata_errors`) that PyAV 19 removed, so every transcription failed. The requirements pin `av<19`; PyAV 17 and 18 still accept the argument.

## Limitations and next steps

This is a deliberately small solution. For production I would add:

- **Long files:** requests are synchronous, so transcribing a very long file on a CPU can take minutes and hit a client or proxy timeout. Decoded audio takes about 230 MB of memory per hour. I would turn on voice activity detection (`vad_filter=True`) to skip silence, add a size and duration limit to 02 and 03 (only 01 has one today), and stream segments back as they are produced.
- **Concurrent uploads:** move transcription off the request path. The API would save the file, create a job and return `202 Accepted` with a job ID. A queue (Redis with Celery, or AWS SQS) would feed a pool of workers that each load the model once. Workers scale with queue length, and the API returns 429 when the queue is full.
- **Storage:** audio in object storage (S3 or GCS) under `audio/<job_id>`, encrypted, and deleted automatically after a retention period. Job metadata and timestamped segments in PostgreSQL, with a SHA-256 hash of each file to detect duplicate uploads.
- **Retries:** permanent failures (corrupt file, too long) are marked failed and not retried. Temporary failures (worker crash, out of memory, network error) are retried with exponential backoff up to 3 times, then sent to a dead-letter queue. A job is acknowledged only when it finishes, so if a worker crashes, another worker picks the job up.
- **API:** one versioned API with `POST /v1/transcriptions` (returns a job ID), `GET /v1/transcriptions/{id}` (status, text and segments, also as SRT or VTT) and `DELETE /v1/transcriptions/{id}`. It would have optional webhooks, API-key authentication, rate limits and a `/healthz` endpoint.

## Project layout

```
volga-scripts/
├── 01-audio-input/                 POST /upload: accepts and validates WAV or MP3
├── 02-transcription/               POST /transcribe: returns plain text
├── 03-timestamped-transcription/   POST /transcribe: returns text and timestamped segments
│                                   (each folder: app.py, test_app.py, requirements.txt, README.md)
└── samples/                        hello.wav and hello.mp3, used by the tests
```
