"""
Phase 2 - Acquire COCO128, explore, validate, document splits.

Usage (from repo root):
  python ml/scripts/phase2_acquire_explore.py
"""

from __future__ import annotations

import json
import shutil
import zipfile
from collections import Counter
from pathlib import Path
from urllib.request import urlretrieve

import yaml

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
SPLITS = ROOT / "data" / "splits"
REPORTS = ROOT / "docs" / "reports"
DATASET_NAME = "coco128"
ZIP_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128.zip"


def download_coco128() -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    target = RAW / DATASET_NAME
    if (target / "images" / "train2017").exists() and (target / "labels" / "train2017").exists():
        print(f"[ok] Dataset already present: {target}")
        return target

    zip_path = RAW / "coco128.zip"
    print(f"[download] {ZIP_URL}")
    urlretrieve(ZIP_URL, zip_path)

    extract_tmp = RAW / "_extract_tmp"
    if extract_tmp.exists():
        shutil.rmtree(extract_tmp)
    extract_tmp.mkdir(parents=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_tmp)

    # zip usually contains a top-level coco128/ folder
    candidates = list(extract_tmp.glob("**/images/train2017"))
    if not candidates:
        raise RuntimeError("Could not find images/train2017 after extract")
    src_root = candidates[0].parents[1]
    if target.exists():
        shutil.rmtree(target)
    shutil.move(str(src_root), str(target))
    shutil.rmtree(extract_tmp, ignore_errors=True)
    zip_path.unlink(missing_ok=True)
    print(f"[ok] Extracted to {target}")
    return target


def load_coco_names() -> list[str]:
    # Official COCO 80 class names (Ultralytics order)
    return [
        "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
        "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
        "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
        "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
        "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
        "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
        "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
        "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
        "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator",
        "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush",
    ]


def validate_and_explore(dataset_root: Path) -> dict:
    images_dir = dataset_root / "images" / "train2017"
    labels_dir = dataset_root / "labels" / "train2017"
    image_files = sorted(
        [p for p in images_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    )
    label_files = sorted([p for p in labels_dir.iterdir() if p.suffix == ".txt"])

    class_counts: Counter[int] = Counter()
    empty_labels = 0
    bad_boxes = 0
    missing_labels = 0
    orphan_labels = 0

    image_stems = {p.stem for p in image_files}
    label_stems = {p.stem for p in label_files}
    missing_labels = len(image_stems - label_stems)
    orphan_labels = len(label_stems - image_stems)

    for lf in label_files:
        text = lf.read_text(encoding="utf-8").strip()
        if not text:
            empty_labels += 1
            continue
        for line in text.splitlines():
            parts = line.strip().split()
            if len(parts) != 5:
                bad_boxes += 1
                continue
            try:
                cls = int(float(parts[0]))
                vals = [float(x) for x in parts[1:]]
            except ValueError:
                bad_boxes += 1
                continue
            if cls < 0 or cls > 79:
                bad_boxes += 1
                continue
            if any(v < 0 or v > 1 for v in vals):
                bad_boxes += 1
                continue
            class_counts[cls] += 1

    names = load_coco_names()
    top_classes = [
        {"id": cid, "name": names[cid], "count": count}
        for cid, count in class_counts.most_common(15)
    ]

    report = {
        "dataset": DATASET_NAME,
        "source": ZIP_URL,
        "license": "COCO annotations: Creative Commons Attribution 4.0; images from Flickr (various). Research/education use; check COCO terms for commercial.",
        "path": str(dataset_root),
        "num_images": len(image_files),
        "num_label_files": len(label_files),
        "num_instances": int(sum(class_counts.values())),
        "num_classes_present": len(class_counts),
        "missing_labels": missing_labels,
        "orphan_labels": orphan_labels,
        "empty_labels": empty_labels,
        "bad_boxes": bad_boxes,
        "top_classes": top_classes,
        "class_histogram": {names[k]: v for k, v in sorted(class_counts.items())},
        "split_note": "COCO128 ships as a single train2017 folder (~128 images). We treat it as train and use a held-out 20% copy for val in data/splits (no leakage of files across roles for our local pipeline).",
        "limitations": [
            "Very small; metrics are noisy and not comparable to full COCO.",
            "Class imbalance is strong (person dominates).",
            "Not for production accuracy claims.",
        ],
    }
    return report


def write_splits(dataset_root: Path, report: dict) -> None:
    """Create deterministic train/val file lists (80/20) under data/splits.

    Images without a matching label file are excluded and recorded as problematic.
    """
    SPLITS.mkdir(parents=True, exist_ok=True)
    images_dir = dataset_root / "images" / "train2017"
    labels_dir = dataset_root / "labels" / "train2017"
    all_images = sorted(
        [p for p in images_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    )
    usable = [p for p in all_images if (labels_dir / f"{p.stem}.txt").exists()]
    skipped = [p.name for p in all_images if p not in usable]

    n = len(usable)
    n_val = max(1, int(n * 0.2))
    val = usable[:n_val]
    train = usable[n_val:]

    def write_list(path: Path, files: list[Path]) -> None:
        path.write_text("\n".join(str(p.resolve()) for p in files) + "\n", encoding="utf-8")

    write_list(SPLITS / "train.txt", train)
    write_list(SPLITS / "val.txt", val)

    # YOLO data yaml pointing at absolute image lists + shared labels path
    data_yaml = {
        "path": str(dataset_root.resolve()),
        "train": str((SPLITS / "train.txt").resolve()),
        "val": str((SPLITS / "val.txt").resolve()),
        "names": {i: n for i, n in enumerate(load_coco_names())},
    }
    yaml_path = ROOT / "ml" / "configs" / "coco128_local.yaml"
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_path.write_text(yaml.dump(data_yaml, sort_keys=False), encoding="utf-8")

    report["problematic_samples"] = {
        "missing_label_files": skipped,
        "action": "Excluded from train/val splits",
    }
    report["splits"] = {
        "train_images": len(train),
        "val_images": len(val),
        "excluded_images": len(skipped),
        "train_list": str(SPLITS / "train.txt"),
        "val_list": str(SPLITS / "val.txt"),
        "data_yaml": str(yaml_path),
    }


def write_class_chart(report: dict) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("[warn] matplotlib missing; skip class chart")
        return
    top = report["top_classes"][:12]
    names = [c["name"] for c in top]
    counts = [c["count"] for c in top]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(names, counts, color="#38bdf8")
    ax.set_title("COCO128 top classes (instance counts)")
    ax.set_ylabel("instances")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    out = REPORTS / "phase2_class_histogram.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    report["class_chart"] = str(out)
    print(f"[ok] Wrote {out}")


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    root = download_coco128()
    report = validate_and_explore(root)
    write_splits(root, report)
    write_class_chart(report)

    out = REPORTS / "phase2_dataset_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("num_images", "num_instances", "num_classes_present", "bad_boxes", "missing_labels", "splits")}, indent=2))
    print(f"[ok] Wrote {out}")

    # Acceptance checks
    assert report["num_images"] >= 100, "Expected ~128 images"
    assert report["bad_boxes"] == 0, "Found invalid YOLO boxes"
    assert report["splits"]["train_images"] > 0 and report["splits"]["val_images"] > 0
    assert report["splits"]["excluded_images"] == report["missing_labels"]
    print("[PASS] Phase 2 acceptance checks")


if __name__ == "__main__":
    main()
