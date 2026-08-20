"""CPU-friendly scene analysis on top of raw detections."""

from __future__ import annotations

from collections import Counter
from typing import Any

# COCO category groups for richer output than flat class names
CATEGORY_GROUPS: dict[str, set[str]] = {
    "people": {"person"},
    "vehicles": {
        "bicycle",
        "car",
        "motorcycle",
        "airplane",
        "bus",
        "train",
        "truck",
        "boat",
    },
    "animals": {
        "bird",
        "cat",
        "dog",
        "horse",
        "sheep",
        "cow",
        "elephant",
        "bear",
        "zebra",
        "giraffe",
    },
    "food": {
        "banana",
        "apple",
        "sandwich",
        "orange",
        "broccoli",
        "carrot",
        "hot dog",
        "pizza",
        "donut",
        "cake",
        "bottle",
        "wine glass",
        "cup",
        "fork",
        "knife",
        "spoon",
        "bowl",
    },
    "furniture": {
        "chair",
        "couch",
        "bed",
        "dining table",
        "toilet",
        "bench",
    },
    "electronics": {
        "tv",
        "laptop",
        "mouse",
        "remote",
        "keyboard",
        "cell phone",
        "microwave",
        "oven",
        "toaster",
        "sink",
        "refrigerator",
        "clock",
    },
}


def _group_for(class_name: str) -> str:
    for group, names in CATEGORY_GROUPS.items():
        if class_name in names:
            return group
    return "other"


def _confidence_tier(conf: float) -> str:
    if conf >= 0.7:
        return "high"
    if conf >= 0.45:
        return "medium"
    return "low"


def _box_area(bbox: dict[str, float]) -> float:
    return max(0.0, bbox["x2"] - bbox["x1"]) * max(0.0, bbox["y2"] - bbox["y1"])


def _size_label(area: float, image_area: float) -> str:
    if image_area <= 0:
        return "unknown"
    ratio = area / image_area
    if ratio >= 0.25:
        return "large"
    if ratio >= 0.08:
        return "medium"
    return "small"


def _zone(bbox: dict[str, float], w: int, h: int) -> str:
    cx = (bbox["x1"] + bbox["x2"]) / 2
    cy = (bbox["y1"] + bbox["y2"]) / 2
    horiz = "left" if cx < w / 3 else ("right" if cx > 2 * w / 3 else "center")
    vert = "top" if cy < h / 3 else ("bottom" if cy > 2 * h / 3 else "middle")
    return f"{vert}-{horiz}"


def _centers_close(a: dict[str, float], b: dict[str, float], thresh: float) -> bool:
    ax = (a["x1"] + a["x2"]) / 2
    ay = (a["y1"] + a["y2"]) / 2
    bx = (b["x1"] + b["x2"]) / 2
    by = (b["y1"] + b["y2"]) / 2
    dist = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
    return dist < thresh


def enrich_detections(
    detections: list[dict[str, Any]],
    image_width: int,
    image_height: int,
) -> list[dict[str, Any]]:
    image_area = float(image_width * image_height)
    enriched = []
    for d in detections:
        area = _box_area(d["bbox"])
        item = dict(d)
        item["category_group"] = _group_for(d["class_name"])
        item["confidence_tier"] = _confidence_tier(d["confidence"])
        item["relative_size"] = _size_label(area, image_area)
        item["zone"] = _zone(d["bbox"], image_width, image_height)
        item["area_ratio"] = round(area / image_area, 4) if image_area else 0.0
        enriched.append(item)
    return enriched


def build_scene_analysis(
    detections: list[dict[str, Any]],
    image_width: int,
    image_height: int,
) -> dict[str, Any]:
    enriched = enrich_detections(detections, image_width, image_height)
    counts = Counter(d["class_name"] for d in enriched)
    groups = Counter(d["category_group"] for d in enriched)
    tiers = Counter(d["confidence_tier"] for d in enriched)

    people = [d for d in enriched if d["class_name"] == "person"]
    vehicles = [d for d in enriched if d["category_group"] == "vehicles"]

    insights: list[str] = []
    alerts: list[dict[str, str]] = []

    if not enriched:
        caption = "Nothing matched in this photo."
        insights.append(
            "This AI only recognizes common everyday objects "
            "(people, cars, animals, furniture, phones, bottles, etc.)."
        )
        insights.append(
            "Things like picture frames, wall art, or plain walls are usually not in its list — "
            "so a wall of frames can correctly show zero results."
        )
        insights.append(
            "Tip: try Match Strictness = Low, or use a photo with people / animals / furniture / vehicles."
        )
        alerts.append(
            {
                "level": "info",
                "code": "no_known_objects",
                "message": "No known objects found. The model does not detect picture frames or general wall art.",
            }
        )
    else:
        top = counts.most_common(3)
        top_txt = ", ".join(f"{n}× {name}" for name, n in top)
        insights.append(f"Dominant objects: {top_txt}.")

        if groups.get("people", 0) >= 5:
            alerts.append(
                {
                    "level": "warning",
                    "code": "crowd",
                    "message": f"Crowd-like scene: {groups['people']} people detected.",
                }
            )
            insights.append("Scene looks busy with multiple people.")
        elif groups.get("people", 0) >= 2:
            insights.append(f"Multiple people in frame ({groups['people']}).")

        if people and vehicles:
            diag = (image_width**2 + image_height**2) ** 0.5
            near = 0
            for p in people:
                for v in vehicles:
                    if _centers_close(p["bbox"], v["bbox"], thresh=0.25 * diag):
                        near += 1
                        break
            if near:
                alerts.append(
                    {
                        "level": "info",
                        "code": "person_near_vehicle",
                        "message": f"{near} person(s) appear near a vehicle.",
                    }
                )
                insights.append("People and vehicles overlap in the same region — useful for traffic/safety views.")

        large = [d for d in enriched if d["relative_size"] == "large"]
        if large:
            names = ", ".join(sorted({d["class_name"] for d in large}))
            insights.append(f"Foreground / large objects: {names}.")

        low = tiers.get("low", 0)
        if low and low >= max(1, len(enriched) // 2):
            insights.append("Many low-confidence boxes — image may be blurry, dark, or unusual for COCO classes.")

        if groups.get("animals", 0):
            insights.append(f"Animals detected: {groups['animals']}.")
        if groups.get("food", 0):
            insights.append(f"Food / tableware items: {groups['food']}.")
        if groups.get("electronics", 0):
            insights.append(f"Electronics / appliances: {groups['electronics']}.")

    # Human-readable one-liner caption
    if enriched:
        parts = []
        for group, n in groups.most_common():
            if n:
                parts.append(f"{n} {group}")
        caption = "Scene contains " + ", ".join(parts[:4]) + "."

    return {
        "caption": caption,
        "total_objects": len(enriched),
        "unique_classes": len(counts),
        "class_counts": dict(counts.most_common()),
        "category_counts": dict(groups.most_common()),
        "confidence_tiers": dict(tiers),
        "insights": insights,
        "alerts": alerts,
        "detections": enriched,
    }
