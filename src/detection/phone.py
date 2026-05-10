from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from ultralytics import YOLO


@dataclass(slots=True)
class PhoneDetectionResult:
    detected: bool
    confidence: float
    bbox: tuple[int, int, int, int] | None


class PhoneDetector:
    def __init__(self, model_path: str | Path = "yolov8n.pt", confidence: float = 0.35) -> None:
        self.confidence = confidence
        self.model = YOLO(str(model_path))

    def analyze(self, frame: np.ndarray) -> PhoneDetectionResult:
        results = self.model.predict(frame, conf=self.confidence, verbose=False)
        if not results:
            return PhoneDetectionResult(False, 0.0, None)

        best_confidence = 0.0
        best_bbox = None

        for detection in results[0].boxes:
            class_id = int(detection.cls[0])
            label = self.model.names.get(class_id, "")
            if label not in {"cell phone", "mobile phone", "phone"}:
                continue

            confidence = float(detection.conf[0])
            if confidence > best_confidence:
                x1, y1, x2, y2 = detection.xyxy[0].tolist()
                best_confidence = confidence
                best_bbox = (int(x1), int(y1), int(x2), int(y2))

        return PhoneDetectionResult(best_bbox is not None, best_confidence, best_bbox)
