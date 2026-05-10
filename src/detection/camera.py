from __future__ import annotations

import cv2


class CameraError(RuntimeError):
    pass


class CameraStream:
    def __init__(self, camera_index: int = 0) -> None:
        self.camera_index = camera_index
        self.capture = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not self.capture.isOpened():
            raise CameraError(f"No se pudo abrir la cámara {camera_index}")

    def read(self):
        success, frame = self.capture.read()
        if not success:
            return None
        return frame

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()
