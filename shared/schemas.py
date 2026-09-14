from pydantic import BaseModel
from typing import List
from datetime import datetime

class BoundingBox(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float

class PredictionItem(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox
    iou_score: float

class InspectionResponse(BaseModel):
    inspection_id: str
    timestamp: datetime
    filename: str
    anomaly_detected: bool
    confidence: float
    iou_score: float
    status: str
    predictions: List[PredictionItem]
