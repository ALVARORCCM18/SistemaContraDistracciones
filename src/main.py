from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import random
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget

from src.audio.tts import TextToSpeech
from src.config import AppConfig, load_app_config, load_character_catalog
from src.detection.camera import CameraError, CameraStream
from src.detection.drowsiness import DrowsinessDetector
from src.detection.phone import PhoneDetector
from src.stats.session import SessionStatistics
from src.ui.popup import AlertPopup
from src.ui.summary import SessionSummaryDialog


@dataclass(slots=True)
class AlertDecision:
    event_type: str | None = None
    message: str | None = None
    character_name: str | None = None
    image_path: str | None = None


class DistractionMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sistema Anti Distracciones")
        self.setMinimumWidth(460)

        self.config: AppConfig = load_app_config()
        self.characters = load_character_catalog(self.config.characters_file)
        self.stats = SessionStatistics()
        self.tts = TextToSpeech()
        self.camera: CameraStream | None = None
        self.drowsiness_detector: DrowsinessDetector | None = None
        self.phone_detector: PhoneDetector | None = None
        self.paused = False
        self.temp_disable_active = False
        self.last_alert_at = datetime.min
        self._session_finished = False

        root = QWidget(self)
        layout = QVBoxLayout(root)

        self.status_label = QLabel("Estado: listo para iniciar")
        self.summary_label = QLabel("Resumen: sin datos todavía")
        self.summary_label.setWordWrap(True)

        button_row = QHBoxLayout()
        self.start_button = QPushButton("Iniciar")
        self.pause_button = QPushButton("Pausar")
        self.disable_button = QPushButton("Desactivar 5 min")
        self.stop_button = QPushButton("Finalizar")
        self.pause_button.setEnabled(False)
        self.disable_button.setEnabled(False)
        self.stop_button.setEnabled(False)

        self.start_button.clicked.connect(self.start_session)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.disable_button.clicked.connect(self.disable_temporarily)
        self.stop_button.clicked.connect(self.stop_session)

        button_row.addWidget(self.start_button)
        button_row.addWidget(self.pause_button)
        button_row.addWidget(self.disable_button)
        button_row.addWidget(self.stop_button)

        layout.addWidget(self.status_label)
        layout.addWidget(self.summary_label)
        layout.addLayout(button_row)
        self.setCentralWidget(root)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_frame)

    def start_session(self) -> None:
        if self.camera is not None:
            return

        try:
            self.camera = CameraStream(self.config.camera_index)
        except CameraError as exc:
            QMessageBox.critical(self, "Error de cámara", str(exc))
            return

        self.drowsiness_detector = DrowsinessDetector(
            ear_threshold=self.config.drowsiness_eye_aspect_ratio_threshold,
            consecutive_frames=self.config.drowsiness_consecutive_frames,
        )
        self.phone_detector = PhoneDetector(confidence=self.config.phone_detection_confidence)
        self.paused = False
        self.status_label.setText("Estado: vigilando la sesión")
        self.summary_label.setText("Resumen: sesión en curso")
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.disable_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.timer.start(int(self.config.detection_interval_seconds * 1000))

    def toggle_pause(self) -> None:
        if self.camera is None or self.temp_disable_active:
            return

        self.paused = not self.paused
        if self.paused:
            self.stats.pause()
            self.status_label.setText("Estado: en pausa")
            self.pause_button.setText("Reanudar")
        else:
            self.stats.resume()
            self.status_label.setText("Estado: vigilando la sesión")
            self.pause_button.setText("Pausar")

    def disable_temporarily(self, minutes: int = 5) -> None:
        if self.camera is None or self.temp_disable_active:
            return

        self.temp_disable_active = True
        self.paused = True
        self.stats.pause()
        self.status_label.setText(f"Estado: desactivado temporalmente ({minutes} min)")
        self.pause_button.setEnabled(False)
        self.disable_button.setEnabled(False)
        self.pause_button.setText("Pausar")
        QTimer.singleShot(minutes * 60 * 1000, self.resume_after_temporary_disable)

    def resume_after_temporary_disable(self) -> None:
        if self.camera is None:
            return

        self.temp_disable_active = False
        self.paused = False
        self.stats.resume()
        self.status_label.setText("Estado: vigilando la sesión")
        self.pause_button.setEnabled(True)
        self.disable_button.setEnabled(True)
        self.pause_button.setText("Pausar")

    def stop_session(self) -> None:
        self.close()

    def process_frame(self) -> None:
        if self.camera is None or self.paused:
            return

        frame = self.camera.read()
        if frame is None:
            return

        decision = self._analyze_frame(frame)
        if decision.event_type and decision.message and decision.character_name:
            now = datetime.now()
            if now - self.last_alert_at >= timedelta(seconds=self.config.alert_cooldown_seconds):
                self.last_alert_at = now
                self.stats.register_event(decision.event_type, decision.message, decision.character_name)
                self.summary_label.setText(f"Resumen: {self.stats.summary()}")
                self._show_alert(decision)

    def closeEvent(self, event) -> None:
        self._shutdown()
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        event.accept()

    def _analyze_frame(self, frame) -> AlertDecision:
        if self.drowsiness_detector is None or self.phone_detector is None:
            return AlertDecision()

        drowsiness = self.drowsiness_detector.analyze(frame)
        if drowsiness.is_drowsy:
            return self._build_decision("drowsiness")

        phone = self.phone_detector.analyze(frame)
        if phone.detected:
            return self._build_decision("phone")

        return AlertDecision()

    def _build_decision(self, event_type: str) -> AlertDecision:
        candidates = self.characters.get(event_type, [])
        if not candidates:
            default_message = "Mantente atento."
            return AlertDecision(event_type, default_message, "Sistema", None)

        character = random.choice(candidates)
        message = random.choice(character.phrases) if character.phrases else "Mantente atento."
        return AlertDecision(event_type, message, character.name, character.image)

    def _show_alert(self, decision: AlertDecision) -> None:
        title = "Distracción detectada" if decision.event_type == "phone" else "Parece que te estás durmiendo"
        popup = AlertPopup(title=title, message=decision.message or "", image_path=decision.image_path)
        if self.config.enable_tts and decision.message:
            self.tts.speak_async(decision.message)
        popup.exec()

    def _shutdown(self) -> int:
        if self._session_finished:
            return 0

        self._session_finished = True
        self.timer.stop()
        self.stats.finish()
        sessions_dir = Path("sessions")
        sessions_dir.mkdir(exist_ok=True)
        report_path = sessions_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.stats.save(report_path)
        summary_dialog = SessionSummaryDialog(self.stats, self)
        summary_dialog.exec()
        self.summary_label.setText(f"Resumen final: {self.stats.summary()}")
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.disable_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        return 0


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    window = DistractionMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
