import builtins
import sys

from shamir_app_core import (
    can_prompt_user,
    confirm_proceed,
    format_banner,
    print_banner,
)


class FakeStdin:
    def __init__(self, interactive):
        self.interactive = interactive

    def isatty(self):
        return self.interactive


def test_format_banner_returns_deterministic_text():
    assert format_banner("Run Import", width=20) == "\n".join(
        [
            "\u250c" + "\u2500" * 18 + "\u2510",
            "\u2502 Run Import       \u2502",
            "\u2514" + "\u2500" * 18 + "\u2518",
        ]
    )


def test_format_banner_works_with_title_only():
    banner = format_banner("Program", width=24)

    assert "Program" in banner
    assert len(banner.splitlines()) == 3


def test_format_banner_works_with_title_and_description():
    banner = format_banner("Program", "Loads order data.", width=32)

    assert "Program" in banner
    assert "Loads order data." in banner
    assert len(banner.splitlines()) == 4


def test_format_banner_wraps_long_description_inside_border():
    banner = format_banner(
        "Program",
        "This description is intentionally long enough to wrap inside the frame.",
        width=28,
    )
    lines = banner.splitlines()

    assert len(lines) > 4
    assert all(len(line) == 28 for line in lines)
    assert all(line.startswith(("\u250c", "\u2502", "\u2514")) for line in lines)
    assert all(line.endswith(("\u2510", "\u2502", "\u2518")) for line in lines)


def test_format_banner_lines_have_consistent_width():
    banner = format_banner("Program", "Short description.", width=36)

    assert {len(line) for line in banner.splitlines()} == {36}


def test_print_banner_prints_formatted_banner(capsys):
    expected = format_banner("Program", "Description.", width=30)

    print_banner("Program", "Description.", width=30)

    assert capsys.readouterr().out == expected + "\n"


def test_can_prompt_user_uses_stdin_isatty(monkeypatch):
    monkeypatch.setattr(sys, "stdin", FakeStdin(True))
    assert can_prompt_user() is True

    monkeypatch.setattr(sys, "stdin", FakeStdin(False))
    assert can_prompt_user() is False


def test_confirm_proceed_returns_true_for_yes_inputs(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda prompt: "y")
    assert confirm_proceed() is True

    monkeypatch.setattr(builtins, "input", lambda prompt: "yes")
    assert confirm_proceed() is True


def test_confirm_proceed_returns_false_for_no_inputs(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda prompt: "n")
    assert confirm_proceed() is False

    monkeypatch.setattr(builtins, "input", lambda prompt: "no")
    assert confirm_proceed() is False


def test_confirm_proceed_respects_default_false_on_empty_input(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda prompt: "")

    assert confirm_proceed(default=False) is False


def test_confirm_proceed_respects_default_true_on_empty_input(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda prompt: "")

    assert confirm_proceed(default=True) is True
