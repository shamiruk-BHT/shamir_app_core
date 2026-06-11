import json
from pathlib import Path

import pytest

from shamir_app_core import JsonlEventWriter


def test_writer_creates_parent_directory(tmp_path: Path):
    path = tmp_path / "nested" / "events.jsonl"

    JsonlEventWriter(path).write({"event_type": "run_summary"})

    assert path.exists()


def test_writer_writes_one_json_line(tmp_path: Path):
    path = tmp_path / "events.jsonl"

    JsonlEventWriter(path).write({"event_type": "run_summary", "count": 1})

    assert path.read_text(encoding="utf-8") == '{"count": 1, "event_type": "run_summary"}\n'


def test_writer_appends_multiple_lines(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    writer = JsonlEventWriter(path)

    writer.write({"event_type": "first"})
    writer.write({"event_type": "second"})

    assert path.read_text(encoding="utf-8").splitlines() == [
        '{"event_type": "first"}',
        '{"event_type": "second"}',
    ]


def test_writer_preserves_non_ascii_text_as_valid_json(tmp_path: Path):
    path = tmp_path / "events.jsonl"

    JsonlEventWriter(path).write({"message": "Zażółć gęślą jaźń"})

    text = path.read_text(encoding="utf-8")
    assert "Zażółć gęślą jaźń" in text
    assert json.loads(text) == {"message": "Zażółć gęślą jaźń"}


def test_writer_preserves_existing_content_when_appending(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    path.write_text('{"existing": true}\n', encoding="utf-8")

    JsonlEventWriter(path).write({"event_type": "new"})

    assert path.read_text(encoding="utf-8").splitlines() == [
        '{"existing": true}',
        '{"event_type": "new"}',
    ]


def test_writer_does_not_mutate_input_event(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    event = {"nested": {"value": 1}, "event_type": "run_summary"}
    original = dict(event)

    JsonlEventWriter(path).write(event)

    assert event == original


def test_writer_rejects_non_mapping_event(tmp_path: Path):
    path = tmp_path / "events.jsonl"

    with pytest.raises(TypeError, match="event must be a mapping"):
        JsonlEventWriter(path).write(["not", "a", "mapping"])


def test_writer_is_available_from_top_level_package():
    assert JsonlEventWriter.__name__ == "JsonlEventWriter"
