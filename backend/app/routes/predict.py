"""Image prediction routes."""

from __future__ import annotations

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.deps import get_engine
from app.schemas import PredictResponse

router = APIRouter(tags=["predict"])

ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp"}


@router.post("/predict", response_model=PredictResponse)
async def predict(
    file: UploadFile = File(...),
    conf: float = Query(0.25, ge=0.01, le=1.0),
    iou: float = Query(0.45, ge=0.01, le=1.0),
):
    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {content_type}")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file upload")

    arr = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    try:
        engine = get_engine()
        result = engine.predict_image(image, conf=conf, iou=iou, return_annotated=False)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc

    return result
