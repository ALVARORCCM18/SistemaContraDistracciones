from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import json


@dataclass(slots=True)
class SessionEvent:
    timestamp: str
    event_type: str
    message: str
    character: str


@dataclass(slots=True)
class SessionStatistics:
    started_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    ended_at: str | None = None
    mobile_distractions: int = 0
    sleep_distractions: int = 0
    paused_seconds: float = 0.0
    events: list[SessionEvent] = field(default_factory=list)
    _pause_started_at: datetime | None = field(default=None, repr=False, compare=False)

    def register_event(self, event_type: str, message: str, character: str) -> None:
        if event_type == "phone":
            self.mobile_distractions += 1
        elif event_type == "drowsiness":
            self.sleep_distractions += 1

        self.events.append(
            SessionEvent(
                timestamp=datetime.now().isoformat(timespec="seconds"),
                event_type=event_type,
                message=message,
                character=character,
            )
        )

    def finish(self) -> None:
        self.resume()
        self.ended_at = datetime.now().isoformat(timespec="seconds")

    def pause(self) -> None:
        if self._pause_started_at is None:
            self._pause_started_at = datetime.now()

    def resume(self) -> None:
        if self._pause_started_at is None:
            return

        self.paused_seconds += (datetime.now() - self._pause_started_at).total_seconds()
        self._pause_started_at = None

    def summary(self) -> str:
        return (
            f"Distracciones por móvil: {self.mobile_distractions}. "
            f"Distracciones por sueño: {self.sleep_distractions}. "
            f"Tiempo en pausa: {self.paused_seconds:.1f} segundos."
        )

    def save(self, path: Path) -> None:
        payload = asdict(self)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
