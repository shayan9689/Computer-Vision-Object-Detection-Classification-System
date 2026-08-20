"""Phase 8 API tests: health + predict."""

from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_predict_rejects_empty():
    response = client.post(
        "/predict",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )
    assert response.status_code == 400


def test_predict_rejects_bad_bytes():
    response = client.post(
        "/predict",
        files={"file": ("bad.jpg", b"not-an-image", "image/jpeg")},
    )
    assert response.status_code == 400


def test_predict_on_sample_image():
    # Prefer a real val image; fall back to a synthetic BGR jpeg
    sample_list = ROOT / "data" / "splits" / "val.txt"
    if sample_list.exists():
        first = sample_list.read_text(encoding="utf-8").splitlines()[0].strip()
        img_path = Path(first)
        content = img_path.read_bytes()
        filename = img_path.name
    else:
        img = np.zeros((240, 320, 3), dtype=np.uint8)
        img[:] = (40, 40, 40)
        ok, buf = cv2.imencode(".jpg", img)
        assert ok
        content = buf.tobytes()
        filename = "synthetic.jpg"

    response = client.post(
        "/predict",
        files={"file": (filename, content, "image/jpeg")},
        params={"conf": 0.25, "iou": 0.45},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "detections" in data
    assert data["image_width"] > 0
    assert data["image_height"] > 0
    assert "model" in data
    for det in data["detections"]:
        assert "class_name" in det
        assert "confidence" in det
        assert "bbox" in det
        box = det["bbox"]
        assert all(k in box for k in ("x1", "y1", "x2", "y2"))
