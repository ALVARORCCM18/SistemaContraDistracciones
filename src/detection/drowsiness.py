from __future__ import annotations

from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np

from src.detection.tracker import choose_closest_face, compute_face_candidate


LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]


@dataclass(slots=True)
class DrowsinessResult:
    is_drowsy: bool
    eye_aspect_ratio: float
    face_present: bool


class DrowsinessDetector:
    def __init__(self, ear_threshold: float = 0.2, consecutive_frames: int = 6) -> None:
        self.ear_threshold = ear_threshold
        self.consecutive_frames = consecutive_frames
        self._frame_counter = 0
        self._face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=0,
            min_detection_confidence=0.5,
        )
        self._mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def analyze(self, frame: np.ndarray) -> DrowsinessResult:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        detection_result = self._face_detection.process(rgb)

        if not detection_result.detections:
            self._frame_counter = 0
            return DrowsinessResult(False, 0.0, False)

        face_candidates = []
        for detection in detection_result.detections:
            relative_bbox = detection.location_data.relative_bounding_box
            width = frame.shape[1]
            height = frame.shape[0]
            x1 = max(0, int(relative_bbox.xmin * width))
            y1 = max(0, int(relative_bbox.ymin * height))
            x2 = min(width, int((relative_bbox.xmin + relative_bbox.width) * width))
            y2 = min(height, int((relative_bbox.ymin + relative_bbox.height) * height))
            face_candidates.append(compute_face_candidate((x1, y1, x2, y2), frame.shape))

        chosen_face = choose_closest_face(face_candidates)
        if chosen_face is None:
            self._frame_counter = 0
            return DrowsinessResult(False, 0.0, False)

        avg_side = max(1.0, chosen_face.face_area ** 0.5)
        x_center = chosen_face.center_x * frame.shape[1]
        y_center = chosen_face.center_y * frame.shape[0]
        x1 = max(0, int(x_center - avg_side / 2))
        y1 = max(0, int(y_center - avg_side / 2))
        x2 = min(frame.shape[1], int(x_center + avg_side / 2))
        y2 = min(frame.shape[0], int(y_center + avg_side / 2))

        if x2 <= x1 or y2 <= y1:
            self._frame_counter = 0
            return DrowsinessResult(False, 0.0, True)

        crop = frame[y1:y2, x1:x2]
        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        result = self._mesh.process(crop_rgb)

        if not result.multi_face_landmarks:
            self._frame_counter = 0
            return DrowsinessResult(False, 0.0, True)

        landmarks = result.multi_face_landmarks[0].landmark
        left_ear = self._eye_aspect_ratio(landmarks, LEFT_EYE, crop.shape)
        right_ear = self._eye_aspect_ratio(landmarks, RIGHT_EYE, crop.shape)
        ear = (left_ear + right_ear) / 2.0

        if ear < self.ear_threshold:
            self._frame_counter += 1
        else:
            self._frame_counter = 0

        return DrowsinessResult(
            is_drowsy=self._frame_counter >= self.consecutive_frames,
            eye_aspect_ratio=ear,
            face_present=True,
        )

    @staticmethod
    def _eye_aspect_ratio(landmarks, eye_indices: list[int], frame_shape: tuple[int, ...]) -> float:
        height, width = frame_shape[:2]

        points = []
        for index in eye_indices:
            landmark = landmarks[index]
            points.append(np.array([landmark.x * width, landmark.y * height], dtype=np.float32))

        p1, p2, p3, p4, p5, p6 = points
        vertical_1 = np.linalg.norm(p2 - p6)
        vertical_2 = np.linalg.norm(p3 - p5)
        horizontal = np.linalg.norm(p1 - p4)
        if horizontal == 0:
            return 0.0
        return (vertical_1 + vertical_2) / (2.0 * horizontal)
