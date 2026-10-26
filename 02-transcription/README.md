# 02 · Transcription

A service that transcribes spoken language in an uploaded audio file into text. It uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) on the CPU. No GPU or PyTorch is needed.

- `POST /transcribe` (multipart field `file`) → `{"text": "..."}`
- Accepts any format FFmpeg can decode (WAV, MP3, M4A, FLAC, …). The language is detected automatically.
- Returns 400 if the file can't be decoded as audio.
- Model: set with `WHISPER_MODEL` (default `base`; also `tiny`, `small`, `medium`, `large-v3`). It downloads on first start.

```bash
pip install -r requirements.txt
uvicorn app:app --port 8002
curl -F file=@../samples/hello.wav localhost:8002/transcribe
# {"text":"Hello world, this is a test of the transcription service. The second sentence comes after a short pause."}
pytest
```
