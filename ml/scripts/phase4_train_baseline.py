"""
Phase 4 - Baseline YOLOv8n training pipeline.

Usage:
  python ml/scripts/phase4_train_baseline.py
"""

from __future__ import annotations

import json
import platform
import shutil
from datetime import datetime, timezone
from pathlib import Path

import torch
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[2]
DATA_YAML = ROOT / "ml" / "configs" / "coco128_local.yaml"
RUNS_DIR = ROOT / "ml" / "runs"
MODELS_DIR = ROOT / "ml" / "models"
REPORTS = ROOT / "docs" / "reports"

# Keep CPU-friendly for local Phase 4
HYPERPARAMS = {
    "model": "yolov8n.pt",
    "epochs": 3,
    "imgsz": 320,
    "batch": 4,
    "device": "cpu",
    "workers": 0,
    "patience": 10,
    "seed": 42,
    "project": str(RUNS_DIR),
    "name": "phase4_baseline",
    "exist_ok": True,
}


def main() -> None:
    assert DATA_YAML.exists(), "Missing data yaml - run Phase 2 first"
    REPORTS.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    print("[train] Loading", HYPERPARAMS["model"])
    model = YOLO(HYPERPARAMS["model"])

    results = model.train(
        data=str(DATA_YAML),
        epochs=HYPERPARAMS["epochs"],
        imgsz=HYPERPARAMS["imgsz"],
        batch=HYPERPARAMS["batch"],
        device=HYPERPARAMS["device"],
        workers=HYPERPARAMS["workers"],
        patience=HYPERPARAMS["patience"],
        seed=HYPERPARAMS["seed"],
        project=HYPERPARAMS["project"],
        name=HYPERPARAMS["name"],
        exist_ok=HYPERPARAMS["exist_ok"],
        verbose=True,
    )

    run_dir = RUNS_DIR / "phase4_baseline"
    best = run_dir / "weights" / "best.pt"
    last = run_dir / "weights" / "last.pt"
    assert best.exists(), f"Missing best checkpoint: {best}"

    dest = MODELS_DIR / "phase4_baseline_best.pt"
    shutil.copy2(best, dest)

    metrics = {}
    if hasattr(results, "results_dict") and results.results_dict:
        metrics = dict(results.results_dict)
    else:
        # fallback: read results.csv last row keys if present
        csv_path = run_dir / "results.csv"
        if csv_path.exists():
            lines = csv_path.read_text(encoding="utf-8").strip().splitlines()
            if len(lines) >= 2:
                headers = [h.strip() for h in lines[0].split(",")]
                values = [v.strip() for v in lines[-1].split(",")]
                metrics = dict(zip(headers, values))

    report = {
        "phase": 4,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hyperparameters": HYPERPARAMS,
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "platform": platform.platform(),
        },
        "checkpoints": {
            "best": str(best),
            "last": str(last),
            "exported": str(dest),
        },
        "metrics": metrics,
    }
    out = REPORTS / "phase4_train_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[ok] Wrote {out}")
    print(f"[ok] Checkpoint: {dest}")
    print("[PASS] Phase 4 acceptance checks")


if __name__ == "__main__":
    main()
