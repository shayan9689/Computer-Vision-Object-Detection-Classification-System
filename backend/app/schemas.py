"""Prediction API schemas."""

from pydantic import BaseModel, Field


class BBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionOut(BaseModel):
    class_id: int
    class_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BBox
    category_group: str | None = None
    confidence_tier: str | None = None
    relative_size: str | None = None
    zone: str | None = None
    area_ratio: float | None = None


class AlertOut(BaseModel):
    level: str
    code: str
    message: str


class AnalysisOut(BaseModel):
    caption: str
    total_objects: int
    unique_classes: int
    class_counts: dict[str, int]
    category_counts: dict[str, int]
    confidence_tiers: dict[str, int]
    insights: list[str]
    alerts: list[AlertOut]


class PredictResponse(BaseModel):
    detections: list[DetectionOut]
    image_width: int
    image_height: int
    model: str
    conf_threshold: float
    iou_threshold: float
    analysis: AnalysisOut | None = None
