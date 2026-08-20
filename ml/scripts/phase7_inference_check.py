"""
Phase 7 - Verify production-style inference engine.

Usage:
  python ml/scripts/phase7_inference_check.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from ml.inference.engine import DetectionEngine  # noqa: E402

REPORTS = ROOT / "docs" / "reports"
SAMPLE_LIST = ROOT / "data" / "splits" / "val.txt"


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    engine = DetectionEngine()

    # Input validation
    try:
        engine.predict_image(np.zeros((10, 10), dtype=np.uint8))
        raise AssertionError("Expected invalid shape to fail")
    except ValueError:
        pass

    try:
        engine.predict_image(ROOT / "does_not_exist.jpg")
        raise AssertionError("Expected missing file to fail")
    except FileNotFoundError:
        pass

    lines = [ln.strip() for ln in SAMPLE_LIST.read_text(encoding="utf-8").splitlines() if ln.strip()]
    sample = Path(lines[0])
    img = cv2.imread(str(sample))
    assert img is not None

    t0 = time.perf_counter()
    out = engine.predict_image(img, conf=0.25, iou=0.45, return_annotated=True)
    latency_ms = (time.perf_counter() - t0) * 1000

    assert "detections" in out
    assert out["image_width"] > 0 and out["image_height"] > 0
    annotated = out.pop("annotated_bgr")
    assert annotated is not None and annotated.ndim == 3

    ann_path = REPORTS / "phase7_sample_annotated.jpg"
    cv2.imwrite(str(ann_path), annotated)

    report = {
        "phase": 7,
        "sample": str(sample),
        "num_detections": len(out["detections"]),
        "latency_ms": latency_ms,
        "model": out["model"],
        "annotated": str(ann_path),
        "thresholds": {"conf": out["conf_threshold"], "iou": out["iou_threshold"]},
        "preview_detections": out["detections"][:5],
    }
    out_path = REPORTS / "phase7_inference_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("num_detections", "latency_ms", "model")}, indent=2))
    print("[PASS] Phase 7 acceptance checks")


if __name__ == "__main__":
    main()
