# Phase 1 — Problem Statement, Scope & Success Metrics

## Problem statement

Build a production-style computer vision web application that **detects objects in images** (bounding boxes + class labels + confidence scores) and exposes that capability through a React frontend and FastAPI backend.

Later phases add video/webcam inference and portfolio packaging. Classification is used as the class-label head inside detection (not a separate whole-image classifier in v1).

## Use case

- **Primary:** User uploads an image → system returns detections overlaid on the image and as structured JSON.
- **Secondary (later):** Video file and optional webcam/live detection.

## Target users

- Portfolio reviewers / hiring managers evaluating end-to-end ML + full-stack skills.
- Developers learning a complete CV system (data → model → API → UI → deploy).

## Exact project scope (v1)

| In scope | Out of scope (for now) |
|----------|-------------------------|
| Image upload + object detection | Separate standalone image-only classifier product |
| Bounding boxes, labels, confidence | Instance segmentation / tracking |
| FastAPI inference API | Mobile apps |
| React UI with visualization | Multi-user auth / billing |
| Trainable detection pipeline (Phases 2–6) | Real-time multi-camera systems |
| Local development first | Mandatory cloud GPU training |

## Dataset direction

| Item | Choice |
|------|--------|
| **Initial dataset** | [COCO128](https://docs.ultralytics.com/datasets/detect/coco128/) (small COCO subset for fast experiments) |
| **Why** | Standard detection format (YOLO), small enough for local CPU/GPU iteration, clear upgrade path to full COCO or a custom set |
| **Object classes** | COCO 80 classes (person, car, dog, bottle, etc.) for pretrained baseline; Phase 2 may narrow to a curated subset if we specialize |
| **License note** | COCO is for research/non-commercial-friendly use under Creative Commons; document license in Phase 2 |

## Detection / classification approach

| Item | Choice |
|------|--------|
| **Task** | Object detection (localize + classify each instance) |
| **Framework** | PyTorch |
| **Model family** | YOLOv8 (Ultralytics) — start with `yolov8n` (nano) for speed |
| **Training plan** | Fine-tune pretrained weights on chosen dataset (Phases 4–6) |
| **Inference** | Python module behind FastAPI; returns boxes in image coordinates |

## Success metrics & acceptance criteria

### Product / system metrics

| Metric | Target (initial) |
|--------|------------------|
| End-to-end image inference | Works locally via UI → API → model |
| API response | JSON with `class`, `confidence`, `bbox` per detection |
| UI | Overlay boxes + labels + scores on uploaded image |
| Latency (local, nano model) | Preferable &lt; 2s per image on typical laptop (GPU optional) |

### Model metrics (evaluated in Phase 5+)

| Metric | Notes |
|--------|-------|
| mAP@0.5 | Primary detection quality |
| Precision / Recall | Per-class and overall |
| IoU | Box quality vs ground truth |

### Phase 1 gate (this phase)

- [x] Problem statement and scope defined
- [x] Dataset direction and classes selected
- [x] Architecture documented
- [x] Repository structure created
- [x] Python and React environments configured (local, no venv)
- [x] README and Git workflow established
- [ ] Confirmed complete by review before any training (Phase 4)

## Explicit non-goals for Phase 1

- No dataset download yet (Phase 2)
- No model training (Phase 4)
- No production deploy (Phase 11)
