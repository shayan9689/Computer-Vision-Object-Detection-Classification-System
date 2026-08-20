# Phase 4 - Baseline Model & Training Pipeline

## Status: PASS (auto-verified)

- Architecture: YOLOv8n pretrained
- Epochs: 3 | imgsz: 320 | batch: 4 | device: CPU
- Checkpoint: `ml/models/phase4_baseline_best.pt`
- Report: `docs/reports/phase4_train_report.json`

## Baseline metrics (from training val)

| Metric | Value |
|--------|-------|
| Precision | ~0.82 |
| Recall | ~0.50 |
| mAP@0.5 | ~0.65 |
| mAP@0.5:0.95 | ~0.48 |
