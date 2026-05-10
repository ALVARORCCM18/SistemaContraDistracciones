from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout


class AlertPopup(QDialog):
    def __init__(self, title: str, message: str, image_path: str | Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(Qt.ApplicationModal)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(180)

        if image_path:
            path = Path(image_path)
            if path.exists():
                pixmap = QPixmap(str(path))
                self.image_label.setPixmap(pixmap.scaledToWidth(260, Qt.SmoothTransformation))
            else:
                self.image_label.setText("[Imagen del personaje]")
        else:
            self.image_label.setText("[Imagen del personaje]")

        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignCenter)

        button_row = QHBoxLayout()
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)
        button_row.addStretch(1)
        button_row.addWidget(close_button)
        button_row.addStretch(1)

        layout.addWidget(self.image_label)
        layout.addWidget(self.message_label)
        layout.addLayout(button_row)
