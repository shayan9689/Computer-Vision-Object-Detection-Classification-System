"""Unit tests for scene analysis (CPU, no model load)."""

from ml.inference.analysis import build_scene_analysis


def test_scene_analysis_counts_and_caption():
    dets = [
        {
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.9,
            "bbox": {"x1": 10, "y1": 10, "x2": 100, "y2": 200},
        },
        {
            "class_id": 0,
            "class_name": "person",
            "confidence": 0.8,
            "bbox": {"x1": 120, "y1": 20, "x2": 200, "y2": 220},
        },
        {
            "class_id": 2,
            "class_name": "car",
            "confidence": 0.75,
            "bbox": {"x1": 50, "y1": 150, "x2": 250, "y2": 280},
        },
    ]
    analysis = build_scene_analysis(dets, 320, 320)
    assert analysis["total_objects"] == 3
    assert analysis["class_counts"]["person"] == 2
    assert analysis["category_counts"]["people"] == 2
    assert analysis["category_counts"]["vehicles"] == 1
    assert "Scene contains" in analysis["caption"]
    assert len(analysis["insights"]) >= 1
    assert analysis["detections"][0]["confidence_tier"] == "high"
    assert analysis["detections"][0]["zone"]
