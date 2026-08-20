# Phase 10 - Video / Real-Time Detection

## Status: PASS (API tested)

- `POST /predict/video` — frame-stride processing, latency + FPS
- Webcam: capture frame in browser → existing `/predict`
- Engine method: `DetectionEngine.predict_video`

```bash
cd backend && pytest tests/test_video.py -q
```
