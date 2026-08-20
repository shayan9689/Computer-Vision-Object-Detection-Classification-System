# System Architecture

## Overview

```
User
  │
  ▼
React.js (Vite + Tailwind)     ← frontend/   host later: Vercel
  │  multipart image upload
  │  GET /health
  ▼
FastAPI                        ← backend/    host later: Railway
  │  CORS enabled for frontend origin
  │  validates image, calls inference
  ▼
Inference engine               ← ml/ (Phases 7+)
  │  YOLOv8 / PyTorch
  ▼
Predictions (JSON)
  class, confidence, bbox [x1,y1,x2,y2]
  │
  ▼
React visualization
  canvas/overlay bounding boxes + labels
```

## Repository layout

```
/
├── frontend/          # React + Vite + Tailwind UI
├── backend/           # FastAPI API
│   └── app/
├── ml/                # Training configs, scripts, saved models (later)
├── data/              # Raw / processed / splits (gitignored contents)
├── docs/              # Architecture, phase docs
├── scripts/           # Helper scripts
└── README.md
```

## Component responsibilities

| Component | Responsibility |
|-----------|----------------|
| **frontend** | Upload UI, call API, render boxes/scores, loading/error states |
| **backend** | HTTP API, CORS, validation, health check, call ML inference |
| **ml** | Dataset configs, train/eval scripts, checkpoints, inference module |
| **data** | Local datasets only — never commit large binaries |

## API contract (planned)

### `GET /health`

```json
{ "status": "ok", "service": "cv-detection-api" }
```

### `POST /predict` (Phase 8)

- **Request:** `multipart/form-data` with `file` (image)
- **Response:**

```json
{
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.92,
      "bbox": { "x1": 10, "y1": 20, "x2": 200, "y2": 400 }
    }
  ],
  "image_width": 640,
  "image_height": 480,
  "model": "yolov8n"
}
```

## Local development (this project)

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- No Python virtualenv — packages installed into the local Python environment
- Model inference always goes through FastAPI (frontend never loads weights)

## Deployment (Phase 11 — not now)

| Layer | Platform |
|-------|----------|
| Frontend | Vercel |
| Backend + model serving | Railway |
| Source of truth | GitHub monorepo |

## Data / model flow (later phases)

1. Acquire & split data → `data/`
2. Train → checkpoints in `ml/models/`
3. Inference module loads best weights
4. FastAPI wraps inference for the React app
