"""Small console-mode helpers for migrated programs."""

import sys
import textwrap


def _wrap_banner_text(value, width):
    wrapped = []
    for line in str(value).splitlines() or [""]:
        wrapped.extend(textwrap.wrap(line, width) or [""])
    return wrapped


def format_banner(title, description=None, width=80):
    """Return a framed banner with wrapped text."""
    if width < 4:
        raise ValueError("Banner width must be at least 4")

    content_width = width - 4
    border_width = width - 2
    lines = _wrap_banner_text(title, content_width)

    if description:
        lines.extend(_wrap_banner_text(description, content_width))

    top = "\u250c" + "\u2500" * border_width + "\u2510"
    bottom = "\u2514" + "\u2500" * border_width + "\u2518"
    body = ["\u2502 " + line.ljust(content_width) + " \u2502" for line in lines]

    return "\n".join([top, *body, bottom])


def print_banner(title, description=None, width=80):
    """Print a formatted banner."""
    print(format_banner(title, description=description, width=width))


def can_prompt_user():
    """Return True when stdin appears interactive."""
    return sys.stdin.isatty()


def confirm_proceed(prompt="Proceed?", default=False):
    """Prompt the user to confirm whether execution should continue."""
    response = input(f"{prompt} ").strip().lower()

    if response == "":
        return bool(default)
    if response in {"y", "yes"}:
        return True
    if response in {"n", "no"}:
        return False
    return bool(default)
