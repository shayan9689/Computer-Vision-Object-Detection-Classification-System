"""Lazy singleton for DetectionEngine used by API routes."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.inference.engine import DetectionEngine

_engine: DetectionEngine | None = None


def get_engine() -> DetectionEngine:
    global _engine
    if _engine is None:
        _engine = DetectionEngine()
    return _engine
