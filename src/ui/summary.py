from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout

from src.stats.session import SessionStatistics


class SessionSummaryDialog(QDialog):
    def __init__(self, statistics: SessionStatistics, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Resumen de la sesión")
        self.setMinimumWidth(520)
        self.setModal(True)

        layout = QVBoxLayout(self)

        headline = QLabel("Resumen final de la sesión")
        headline.setAlignment(Qt.AlignCenter)

        stats_label = QLabel(statistics.summary())
        stats_label.setWordWrap(True)

        events_label = QLabel("Eventos detectados")
        events_label.setAlignment(Qt.AlignLeft)

        events_view = QTextEdit()
        events_view.setReadOnly(True)
        if statistics.events:
            lines = []
            for event in statistics.events:
                lines.append(f"[{event.timestamp}] {event.event_type} - {event.character}: {event.message}")
            events_view.setPlainText("\n".join(lines))
        else:
            events_view.setPlainText("No se detectaron distracciones durante esta sesión.")

        close_row = QHBoxLayout()
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.accept)
        close_row.addStretch(1)
        close_row.addWidget(close_button)
        close_row.addStretch(1)

        layout.addWidget(headline)
        layout.addWidget(stats_label)
        layout.addWidget(events_label)
        layout.addWidget(events_view)
        layout.addLayout(close_row)
