"""Production-style inference engine for object detection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[2]
PRETRAINED = ROOT / "ml" / "models" / "pretrained_yolov8n.pt"
FINE_TUNED = ROOT / "ml" / "models" / "best.pt"
FALLBACK_WEIGHTS = ROOT / "ml" / "models" / "phase4_baseline_best.pt"


def resolve_weights(weights: str | Path | None = None) -> Path:
    """Prefer official pretrained nano weights on CPU for general photos.

    Short fine-tunes on tiny COCO128 often look worse on everyday images.
    """
    if weights:
        path = Path(weights)
        if not path.exists():
            raise FileNotFoundError(f"Model weights not found: {path}")
        return path
    for candidate in (PRETRAINED, FINE_TUNED, FALLBACK_WEIGHTS):
        if candidate.exists():
            return candidate
    raise FileNotFoundError("No model weights found under ml/models/")



@dataclass
class Detection:
    class_id: int
    class_name: str
    confidence: float
    bbox: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox": self.bbox,
        }


class DetectionEngine:
    """Reusable image inference wrapper around YOLOv8."""

    def __init__(
        self,
        weights: str | Path | None = None,
        conf: float = 0.25,
        iou: float = 0.45,
        imgsz: int = 416,
        device: str = "cpu",
    ) -> None:
        path = resolve_weights(weights)
        if not path.exists():
            raise FileNotFoundError(f"Model weights not found: {path}")
        self.weights = path
        self.conf = conf
        self.iou = iou
        self.imgsz = imgsz
        self.device = device
        self.model = YOLO(str(path))
        self.names = self.model.names

    def predict_image(
        self,
        image: np.ndarray | str | Path,
        conf: float | None = None,
        iou: float | None = None,
        return_annotated: bool = False,
    ) -> dict[str, Any]:
        if isinstance(image, (str, Path)):
            image_path = Path(image)
            if not image_path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            source: Any = str(image_path)
        else:
            if not isinstance(image, np.ndarray):
                raise TypeError("image must be a numpy array or path")
            if image.ndim != 3 or image.shape[2] != 3:
                raise ValueError("image array must be HxWx3")
            source = image

        conf_thr = self.conf if conf is None else conf
        iou_thr = self.iou if iou is None else iou

        results = self.model.predict(
            source=source,
            conf=conf_thr,
            iou=iou_thr,
            imgsz=self.imgsz,
            device=self.device,
            verbose=False,
        )
        result = results[0]
        h, w = result.orig_shape

        detections: list[Detection] = []
        if result.boxes is not None and len(result.boxes):
            for box in result.boxes:
                cls_id = int(box.cls.item())
                conf_v = float(box.conf.item())
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0].tolist()]
                detections.append(
                    Detection(
                        class_id=cls_id,
                        class_name=str(self.names.get(cls_id, str(cls_id))),
                        confidence=conf_v,
                        bbox={"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    )
                )

        payload: dict[str, Any] = {
            "detections": [d.to_dict() for d in detections],
            "image_width": int(w),
            "image_height": int(h),
            "model": self.weights.name,
            "conf_threshold": conf_thr,
            "iou_threshold": iou_thr,
        }
        # Rich CPU-side analysis (counts, zones, insights) — no GPU needed
        from ml.inference.analysis import build_scene_analysis

        analysis = build_scene_analysis(payload["detections"], int(w), int(h))
        payload["detections"] = analysis.pop("detections")
        payload["analysis"] = analysis

        if return_annotated:
            payload["annotated_bgr"] = result.plot()
        return payload

    def predict_video(
        self,
        video_path: str | Path,
        conf: float | None = None,
        iou: float | None = None,
        stride: int = 5,
        max_frames: int = 60,
    ) -> dict[str, Any]:
        import time

        import cv2

        path = Path(video_path)
        if not path.exists():
            raise FileNotFoundError(f"Video not found: {path}")

        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise ValueError("Could not open video")

        frame_summaries: list[dict[str, Any]] = []
        latencies: list[float] = []
        idx = 0
        processed = 0

        while processed < max_frames:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % stride == 0:
                t0 = time.perf_counter()
                out = self.predict_image(frame, conf=conf, iou=iou, return_annotated=False)
                latencies.append((time.perf_counter() - t0) * 1000)
                top = []
                for d in out["detections"][:5]:
                    top.append(d["class_name"])
                frame_summaries.append(
                    {
                        "frame_index": idx,
                        "num_detections": len(out["detections"]),
                        "top_classes": top,
                    }
                )
                processed += 1
            idx += 1

        cap.release()
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        avg_fps = 1000.0 / avg_latency if avg_latency > 0 else 0.0

        return {
            "frames_processed": processed,
            "stride": stride,
            "max_frames": max_frames,
            "avg_latency_ms": avg_latency,
            "avg_fps": avg_fps,
            "model": self.weights.name,
            "conf_threshold": self.conf if conf is None else conf,
            "iou_threshold": self.iou if iou is None else iou,
            "frame_summaries": frame_summaries,
        }
