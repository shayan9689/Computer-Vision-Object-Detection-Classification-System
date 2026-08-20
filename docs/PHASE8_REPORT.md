# Phase 8 - FastAPI Backend

## Status: PASS (auto-verified)

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Health check |
| POST | `/predict` | Image upload inference (multipart `file`) |
| GET | `/docs` | OpenAPI docs |

## Acceptance

- Image-upload inference endpoint wired to `DetectionEngine`
- Clean JSON response with detections + image size + model name
- CORS enabled for React (`localhost:5173`)
- Validation/errors for empty/invalid uploads
- Local tests: `cd backend && pytest` (5 passed)

## Run

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
