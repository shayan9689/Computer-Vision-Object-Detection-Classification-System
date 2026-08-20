# Phase 2 - Dataset Acquisition & Exploration

## Status: PASS (auto-verified)

## Actions completed

- Downloaded COCO128 into `data/raw/coco128`
- Validated YOLO label format (normalized xywh)
- Built class histogram and top-class summary
- Created deterministic 80/20 train/val lists in `data/splits/`
- Wrote Ultralytics data config: `ml/configs/coco128_local.yaml`
- Documented license and limitations in `docs/reports/phase2_dataset_report.json`

## Acceptance criteria

| Criterion | Result |
|-----------|--------|
| Dataset acquired and organized | PASS |
| Class distribution inspected | PASS |
| Annotations validated | PASS (0 bad boxes) |
| Problematic samples identified | PASS (missing labels excluded from splits) |
| Train/val splits created | PASS |
| Source/license/limitations documented | PASS |

## How to re-run

```bash
python ml/scripts/phase2_acquire_explore.py
```
