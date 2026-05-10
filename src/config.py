from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
DEFAULT_CHARACTERS_FILE = ASSETS_DIR / "characters.json"


@dataclass(slots=True)
class CharacterSet:
    name: str
    image: str
    voice: str
    phrases: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AppConfig:
    camera_index: int = 0
    detection_interval_seconds: float = 0.2
    alert_cooldown_seconds: float = 8.0
    drowsiness_eye_aspect_ratio_threshold: float = 0.2
    drowsiness_consecutive_frames: int = 6
    phone_detection_confidence: float = 0.35
    face_search_confidence: float = 0.5
    enable_tts: bool = True
    characters_file: Path = DEFAULT_CHARACTERS_FILE


def load_app_config() -> AppConfig:
    return AppConfig()


def load_character_catalog(path: Path | None = None) -> dict[str, list[CharacterSet]]:
    catalog_path = path or DEFAULT_CHARACTERS_FILE
    if not catalog_path.exists():
        return {"drowsiness": [], "phone": []}

    raw = json.loads(catalog_path.read_text(encoding="utf-8"))
    return {
        "drowsiness": [_parse_character(item) for item in raw.get("drowsiness", [])],
        "phone": [_parse_character(item) for item in raw.get("phone", [])],
    }


def _parse_character(data: dict[str, Any]) -> CharacterSet:
    return CharacterSet(
        name=str(data.get("name", "")),
        image=str(data.get("image", "")),
        voice=str(data.get("voice", "")),
        phrases=[str(item) for item in data.get("phrases", [])],
    )
