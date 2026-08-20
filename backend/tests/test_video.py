"""Extra Phase 10/11 API tests."""

from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def _make_tiny_video(path: Path, frames: int = 8) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 5, (160, 120))
    assert writer.isOpened()
    for i in range(frames):
        frame = np.zeros((120, 160, 3), dtype=np.uint8)
        frame[:] = (30 + i * 5, 40, 50)
        cv2.rectangle(frame, (20, 20), (80, 80), (0, 200, 255), -1)
        writer.write(frame)
    writer.release()


def test_predict_video_on_synthetic():
    tmp = ROOT / "data" / "processed" / "phase10_tiny.mp4"
    _make_tiny_video(tmp)
    content = tmp.read_bytes()
    response = client.post(
        "/predict/video",
        files={"file": ("tiny.mp4", content, "video/mp4")},
        params={"conf": 0.25, "stride": 2, "max_frames": 4},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["frames_processed"] >= 1
    assert "avg_fps" in data
    assert "frame_summaries" in data
