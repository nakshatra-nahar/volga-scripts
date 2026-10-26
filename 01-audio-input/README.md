# 01 · Audio input

A service that accepts an audio file (WAV or MP3), validates it, and stores it.

- `POST /upload` (multipart field `file`)
- The format is detected from the file's bytes, not its name, so a renamed text file is rejected.
- Limit: 25 MB. Files are saved as `uploads/<id>.<wav|mp3>`. The client's filename is never used as a path.

| Status | Meaning |
|---|---|
| 200 | `{"id", "filename", "format", "size_bytes"}` |
| 413 | File larger than 25 MB |
| 415 | Not WAV or MP3 |

```bash
pip install -r requirements.txt
uvicorn app:app --port 8001
curl -F file=@../samples/hello.mp3 localhost:8001/upload
# {"id":"3f2c…","filename":"hello.mp3","format":"mp3","size_bytes":28304}
pytest
```
