"""
Phase 6 - Short improvement run from Phase 4 checkpoint; pick best model.

Usage:
  python ml/scripts/phase6_improve.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[2]
DATA_YAML = ROOT / "ml" / "configs" / "coco128_local.yaml"
BASE = ROOT / "ml" / "models" / "phase4_baseline_best.pt"
MODELS = ROOT / "ml" / "models"
REPORTS = ROOT / "docs" / "reports"
RUNS = ROOT / "ml" / "runs"


def load_map50(report_path: Path) -> float:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    return float(data["summary"]["map50"])


def main() -> None:
    assert BASE.exists(), "Missing Phase 4 baseline"
    REPORTS.mkdir(parents=True, exist_ok=True)

    # Improvement: continue training a few more epochs with slightly larger imgsz
    model = YOLO(str(BASE))
    model.train(
        data=str(DATA_YAML),
        epochs=2,
        imgsz=416,
        batch=4,
        device="cpu",
        workers=0,
        seed=42,
        project=str(RUNS),
        name="phase6_improve",
        exist_ok=True,
        lr0=0.001,
        mosaic=0.5,
    )

    improved_best = RUNS / "phase6_improve" / "weights" / "best.pt"
    assert improved_best.exists()

    # Evaluate improved
    eval_model = YOLO(str(improved_best))
    metrics = eval_model.val(
        data=str(DATA_YAML),
        imgsz=416,
        batch=4,
        device="cpu",
        workers=0,
        project=str(RUNS),
        name="phase6_eval",
        exist_ok=True,
    )
    improved_map50 = float(metrics.box.map50)
    baseline_map50 = load_map50(REPORTS / "phase5_eval_report.json")

    # Select best by mAP50
    if improved_map50 >= baseline_map50:
        chosen = improved_best
        chosen_name = "phase6_improved"
        reason = "phase6 mAP50 >= phase4/5 baseline"
    else:
        chosen = BASE
        chosen_name = "phase4_baseline"
        reason = "baseline mAP50 higher; keep phase4 weights"

    dest = MODELS / "best.pt"
    shutil.copy2(chosen, dest)
    shutil.copy2(improved_best, MODELS / "phase6_improved_best.pt")

    # Quick latency probe
    import time
    import numpy as np

    dummy = np.zeros((416, 416, 3), dtype=np.uint8)
    infer = YOLO(str(dest))
    t0 = time.perf_counter()
    infer.predict(dummy, imgsz=416, device="cpu", verbose=False)
    latency_ms = (time.perf_counter() - t0) * 1000

    report = {
        "phase": 6,
        "baseline_map50": baseline_map50,
        "improved_map50": improved_map50,
        "selected_model": chosen_name,
        "selected_path": str(dest),
        "selection_reason": reason,
        "latency_ms_cpu_dummy": latency_ms,
        "hyperparams": {
            "epochs": 2,
            "imgsz": 416,
            "batch": 4,
            "lr0": 0.001,
            "mosaic": 0.5,
            "device": "cpu",
        },
    }
    out = REPORTS / "phase6_improve_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    assert dest.exists()
    print("[PASS] Phase 6 acceptance checks")


if __name__ == "__main__":
    main()
