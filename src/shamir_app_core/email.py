"""Generic text email helpers without delivery side effects."""

from dataclasses import dataclass
from collections.abc import Iterable
from typing import TextIO


@dataclass(frozen=True)
class EmailMessage:
    """A simple validated text email message."""

    to: tuple[str, ...]
    subject: str
    body_text: str

    def __init__(self, to: Iterable[str], subject: str, body_text: str) -> None:
        clean_subject = _require_non_blank(subject, "subject")
        clean_body_text = _require_non_blank(body_text, "body_text", strip=False)
        clean_to = _clean_recipients(to)

        object.__setattr__(self, "to", clean_to)
        object.__setattr__(self, "subject", clean_subject)
        object.__setattr__(self, "body_text", clean_body_text)


class ConsoleEmailSender:
    """Write a readable email preview to a text stream."""

    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    def send(self, message: EmailMessage) -> None:
        """Write the message preview to the configured stream."""
        self.stream.write("--- Email preview ---\n")
        self.stream.write(f"To: {', '.join(message.to)}\n")
        self.stream.write(f"Subject: {message.subject}\n")
        self.stream.write("\n")
        self.stream.write(message.body_text)
        if not message.body_text.endswith("\n"):
            self.stream.write("\n")
        self.stream.write("--- End email preview ---\n")


def _require_non_blank(value: str, field_name: str, *, strip: bool = True) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must not be blank")
    if strip:
        return value.strip()
    return value


def _clean_recipients(recipients: Iterable[str]) -> tuple[str, ...]:
    if isinstance(recipients, str):
        raise ValueError("to recipients must be provided as an iterable of strings")

    clean_recipients = tuple(
        _require_non_blank(recipient, "recipients") for recipient in recipients
    )
    if not clean_recipients:
        raise ValueError("at least one to recipient is required")
    return clean_recipients


__all__ = [
    "ConsoleEmailSender",
    "EmailMessage",
]
