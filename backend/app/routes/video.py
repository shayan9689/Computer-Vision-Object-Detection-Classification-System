"""Video prediction routes."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.deps import get_engine

router = APIRouter(tags=["predict"])

ALLOWED_VIDEO = {
    "video/mp4",
    "video/avi",
    "video/x-msvideo",
    "video/quicktime",
    "video/webm",
    "application/octet-stream",
}


class FrameSummary(BaseModel):
    frame_index: int
    num_detections: int
    top_classes: list[str] = Field(default_factory=list)


class VideoPredictResponse(BaseModel):
    frames_processed: int
    stride: int
    max_frames: int
    avg_latency_ms: float
    avg_fps: float
    model: str
    conf_threshold: float
    iou_threshold: float
    frame_summaries: list[FrameSummary]


@router.post("/predict/video", response_model=VideoPredictResponse)
async def predict_video(
    file: UploadFile = File(...),
    conf: float = Query(0.25, ge=0.01, le=1.0),
    iou: float = Query(0.45, ge=0.01, le=1.0),
    stride: int = Query(5, ge=1, le=30),
    max_frames: int = Query(60, ge=1, le=300),
):
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_VIDEO and not content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {content_type}")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file upload")

    suffix = Path(file.filename or "clip.mp4").suffix or ".mp4"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(raw)
            tmp_path = Path(tmp.name)

        engine = get_engine()
        result = engine.predict_video(
            tmp_path,
            conf=conf,
            iou=iou,
            stride=stride,
            max_frames=max_frames,
        )
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Video inference failed: {exc}") from exc
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
