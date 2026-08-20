"""
Phase 3 - Preprocessing and augmentation pipeline (reproducible, no leakage).

- Letterbox resize to model size (640)
- Color normalize to 0-1 (YOLO-style)
- Augment train samples only (flip, brightness, HSV jitter)
- Validate transformed samples and write preview images
- Emit reproducible config JSON

Usage:
  python ml/scripts/phase3_preprocess_augment.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import cv2
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed" / "phase3"
REPORTS = ROOT / "docs" / "reports"
CONFIG_OUT = ROOT / "ml" / "configs" / "preprocess_config.json"
DATA_YAML = ROOT / "ml" / "configs" / "coco128_local.yaml"

DEFAULT_CONFIG = {
    "imgsz": 640,
    "seed": 42,
    "normalize": "0_1",
    "letterbox_color": 114,
    "train_augmentations": {
        "horizontal_flip_p": 0.5,
        "brightness_delta": 0.15,
        "hsv_h": 0.015,
        "hsv_s": 0.4,
        "hsv_v": 0.3,
    },
    "val_augmentations": None,
    "leakage_policy": "Augmentations applied only to samples listed in train.txt; val.txt never augmented for preview/export.",
}


def letterbox(img: np.ndarray, imgsz: int, color: int = 114) -> tuple[np.ndarray, float, tuple[int, int]]:
    h, w = img.shape[:2]
    scale = min(imgsz / h, imgsz / w)
    nh, nw = int(round(h * scale)), int(round(w * scale))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    canvas = np.full((imgsz, imgsz, 3), color, dtype=np.uint8)
    top = (imgsz - nh) // 2
    left = (imgsz - nw) // 2
    canvas[top : top + nh, left : left + nw] = resized
    return canvas, scale, (left, top)


def normalize_01(img: np.ndarray) -> np.ndarray:
    return img.astype(np.float32) / 255.0


def augment_train(img: np.ndarray, cfg: dict, rng: random.Random) -> np.ndarray:
    out = img.copy()
    aug = cfg["train_augmentations"]
    if rng.random() < aug["horizontal_flip_p"]:
        out = cv2.flip(out, 1)

    # brightness
    delta = 1.0 + rng.uniform(-aug["brightness_delta"], aug["brightness_delta"])
    out = np.clip(out.astype(np.float32) * delta, 0, 255).astype(np.uint8)

    # HSV jitter
    hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 0] = (hsv[..., 0] + rng.uniform(-aug["hsv_h"], aug["hsv_h"]) * 180) % 180
    hsv[..., 1] = np.clip(hsv[..., 1] * (1 + rng.uniform(-aug["hsv_s"], aug["hsv_s"])), 0, 255)
    hsv[..., 2] = np.clip(hsv[..., 2] * (1 + rng.uniform(-aug["hsv_v"], aug["hsv_v"])), 0, 255)
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    return out


def load_split_paths(name: str) -> list[Path]:
    path = ROOT / "data" / "splits" / f"{name}.txt"
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return [Path(p) for p in lines]


def process_split(split: str, cfg: dict, n_preview: int = 8) -> dict:
    rng = random.Random(cfg["seed"] + (0 if split == "train" else 1))
    paths = load_split_paths(split)
    out_dir = PROCESSED / split
    out_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    shapes = []
    for i, img_path in enumerate(paths[:n_preview]):
        img = cv2.imread(str(img_path))
        if img is None:
            raise RuntimeError(f"Failed to read {img_path}")
        if split == "train":
            img = augment_train(img, cfg, rng)
        boxed, scale, pad = letterbox(img, cfg["imgsz"], cfg["letterbox_color"])
        norm = normalize_01(boxed)
        assert norm.min() >= 0.0 and norm.max() <= 1.0
        assert boxed.shape == (cfg["imgsz"], cfg["imgsz"], 3)

        out_path = out_dir / f"preview_{i:02d}.jpg"
        cv2.imwrite(str(out_path), boxed)
        saved += 1
        shapes.append({"file": img_path.name, "scale": scale, "pad": list(pad), "out": str(out_path)})

    return {
        "split": split,
        "source_count": len(paths),
        "previews_written": saved,
        "augmented": split == "train",
        "samples": shapes,
    }


def main() -> None:
    assert DATA_YAML.exists(), "Run Phase 2 first (missing coco128_local.yaml)"
    REPORTS.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    cfg = dict(DEFAULT_CONFIG)
    CONFIG_OUT.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    train_stats = process_split("train", cfg)
    val_stats = process_split("val", cfg)

    # Ensure YOLO training config still points at original images (Ultralytics applies its own aug).
    # Our preprocess config documents the policy; no train/val file mixing.
    train_set = set(load_split_paths("train"))
    val_set = set(load_split_paths("val"))
    overlap = train_set & val_set

    report = {
        "config_path": str(CONFIG_OUT),
        "train": train_stats,
        "val": val_stats,
        "leakage_check": {
            "train_val_overlap": len(overlap),
            "pass": len(overlap) == 0,
        },
        "note": "Preview pipeline validates letterbox+normalize+train-only aug. Ultralytics training uses ml/configs/coco128_local.yaml with built-in aug controlled in Phase 4.",
    }
    out = REPORTS / "phase3_preprocess_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["leakage_check"], indent=2))
    print(f"[ok] Wrote {out}")

    assert train_stats["previews_written"] > 0
    assert val_stats["previews_written"] > 0
    assert report["leakage_check"]["pass"]
    assert val_stats["augmented"] is False
    assert train_stats["augmented"] is True
    print("[PASS] Phase 3 acceptance checks")


if __name__ == "__main__":
    main()
