from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FaceCandidate:
    face_area: float
    center_x: float
    center_y: float


def choose_closest_face(candidates: list[FaceCandidate]) -> FaceCandidate | None:
    if not candidates:
        return None
    return max(
        candidates,
        key=lambda item: (
            item.face_area,
            -((item.center_x - 0.5) ** 2 + (item.center_y - 0.5) ** 2),
        ),
    )


def compute_face_candidate(bbox: tuple[int, int, int, int], frame_shape: tuple[int, int, int]) -> FaceCandidate:
    x1, y1, x2, y2 = bbox
    width = max(0, x2 - x1)
    height = max(0, y2 - y1)
    area = float(width * height)
    frame_height, frame_width = frame_shape[:2]
    if frame_width == 0 or frame_height == 0:
        return FaceCandidate(face_area=area, center_x=0.0, center_y=0.0)

    return FaceCandidate(
        face_area=area,
        center_x=((x1 + x2) / 2.0) / frame_width,
        center_y=((y1 + y2) / 2.0) / frame_height,
    )
