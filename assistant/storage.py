from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


APP_NAME = "Brother"
DATA_DIR = Path("data")
STATE_FILE = DATA_DIR / "assistant_state.json"


DEFAULT_STATE: dict[str, Any] = {
    "profile": {
        "name": "Boss",
        "assistant_name": APP_NAME,
        "style": "calm senior-brother mentor: honest, practical, protective, and encouraging",
    },
    "settings": {
        "brain": "rules",
        "ollama_url": "http://localhost:11434/api/generate",
        "ollama_model": "qwen2.5:0.5b",
        "ollama_timeout_seconds": 180,
    },
    "memories": [],
    "tasks": [],
    "journal": [],
    "conversation": [],
}


@dataclass
class AssistantState:
    path: Path = STATE_FILE
    data: dict[str, Any] = field(default_factory=lambda: json.loads(json.dumps(DEFAULT_STATE)))

    def load(self) -> None:
        if not self.path.exists():
            self.save()
            return

        with self.path.open("r", encoding="utf-8") as file:
            loaded = json.load(file)

        self.data = merge_defaults(DEFAULT_STATE, loaded)
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(self.data, file, indent=2)


def merge_defaults(defaults: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(defaults))
    for key, value in current.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_defaults(merged[key], value)
        else:
            merged[key] = value
    return merged
