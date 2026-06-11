"""Append-only JSONL event writing helpers."""

import json
from collections.abc import Mapping
from pathlib import Path


class JsonlEventWriter:
    """Append explicit event records as one JSON object per line."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def write(self, event: Mapping[str, object]) -> None:
        """Append one mapping event to the JSONL file."""
        if not isinstance(event, Mapping):
            raise TypeError("event must be a mapping")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event, ensure_ascii=False, sort_keys=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(f"{line}\n")


__all__ = [
    "JsonlEventWriter",
]
