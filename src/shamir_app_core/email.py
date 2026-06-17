"""Generic text email messages and sender foundations."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Protocol, TextIO
from urllib.parse import quote


@dataclass(frozen=True)
class EmailMessage:
    """A simple validated plain-text email message."""

    to: tuple[str, ...]
    subject: str
    body_text: str

    def __init__(self, to: Iterable[str], subject: str, body_text: str) -> None:
        """Create a message and validate required text fields and recipients."""
        clean_subject = _require_non_blank(subject, "subject")
        clean_body_text = _require_non_blank(body_text, "body_text", strip=False)
        clean_to = _clean_recipients(to)

        object.__setattr__(self, "to", clean_to)
        object.__setattr__(self, "subject", clean_subject)
        object.__setattr__(self, "body_text", clean_body_text)


class ConsoleEmailSender:
    """Write a readable email preview to a text stream."""

    def __init__(self, stream: TextIO) -> None:
        """Create a sender that writes previews to the provided text stream."""
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


class EmailSendError(RuntimeError):
    """Raised when an email sender cannot complete or verify delivery."""


@dataclass(frozen=True)
class GraphEmailSettings:
    """Settings required to request a Graph token and call sendMail."""

    tenant_id: str
    client_id: str
    client_secret: str = field(repr=False)
    sender: str
    timeout_seconds: float = 30.0
    save_to_sent_items: bool = True
    authority_host: str = "https://login.microsoftonline.com"
    graph_host: str = "https://graph.microsoft.com"

    def __post_init__(self) -> None:
        """Normalize string settings and reject invalid timeout values."""
        object.__setattr__(
            self,
            "tenant_id",
            _require_non_blank(self.tenant_id, "tenant_id"),
        )
        object.__setattr__(
            self,
            "client_id",
            _require_non_blank(self.client_id, "client_id"),
        )
        object.__setattr__(
            self,
            "client_secret",
            _require_non_blank(self.client_secret, "client_secret"),
        )
        object.__setattr__(self, "sender", _require_non_blank(self.sender, "sender"))
        object.__setattr__(
            self,
            "authority_host",
            _require_non_blank(self.authority_host, "authority_host").rstrip("/"),
        )
        object.__setattr__(
            self,
            "graph_host",
            _require_non_blank(self.graph_host, "graph_host").rstrip("/"),
        )
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")


class _HttpTransport(Protocol):
    """Minimal POST-only transport interface used by GraphEmailSender."""

    def post(
        self,
        url: str,
        *,
        data: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: float,
    ) -> Any:
        """Send an HTTP POST request and return a response-like object."""


class GraphEmailSender:
    """Send simple text emails through Microsoft Graph using an injected transport."""

    def __init__(self, settings: GraphEmailSettings, transport: _HttpTransport) -> None:
        """Create a Graph sender with explicit settings and HTTP transport."""
        self.settings = settings
        self.transport = transport

    def send(self, message: EmailMessage) -> None:
        """Request a token, call Graph sendMail, and require HTTP 202 success."""
        access_token = self._request_access_token()
        try:
            response = self.transport.post(
                self._send_mail_url(),
                json=self._send_mail_payload(message),
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                timeout_seconds=self.settings.timeout_seconds,
            )
        except Exception as exc:
            raise EmailSendError("Graph sendMail request failed") from exc

        status_code = _response_status_code(response)
        if status_code != 202:
            raise EmailSendError(f"Graph sendMail failed with HTTP {status_code}")

    def _request_access_token(self) -> str:
        """Request an OAuth client-credentials token and return the access token."""
        try:
            response = self.transport.post(
                self._token_url(),
                data={
                    "client_id": self.settings.client_id,
                    "client_secret": self.settings.client_secret,
                    "grant_type": "client_credentials",
                    "scope": "https://graph.microsoft.com/.default",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout_seconds=self.settings.timeout_seconds,
            )
        except Exception as exc:
            raise EmailSendError("OAuth token request transport failed") from exc

        status_code = _response_status_code(response)
        if status_code != 200:
            raise EmailSendError(f"OAuth token request failed with HTTP {status_code}")

        body = _response_json(response)
        access_token = body.get("access_token")
        if not isinstance(access_token, str) or not access_token.strip():
            raise EmailSendError("OAuth token response did not include access_token")
        return access_token

    def _token_url(self) -> str:
        """Build the OAuth token endpoint URL for the configured tenant."""
        return (
            f"{self.settings.authority_host}/{self.settings.tenant_id}"
            "/oauth2/v2.0/token"
        )

    def _send_mail_url(self) -> str:
        """Build the Graph sendMail endpoint URL for the configured sender."""
        sender = quote(self.settings.sender, safe="")
        return f"{self.settings.graph_host}/v1.0/users/{sender}/sendMail"

    def _send_mail_payload(self, message: EmailMessage) -> dict[str, Any]:
        """Convert an EmailMessage into the Graph sendMail JSON payload."""
        return {
            "message": {
                "subject": message.subject,
                "body": {
                    "contentType": "Text",
                    "content": message.body_text,
                },
                "toRecipients": [
                    {"emailAddress": {"address": recipient}}
                    for recipient in message.to
                ],
            },
            "saveToSentItems": self.settings.save_to_sent_items,
        }


def _require_non_blank(value: str, field_name: str, *, strip: bool = True) -> str:
    """Return a validated non-blank string, optionally stripped."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must not be blank")
    if strip:
        return value.strip()
    return value


def _clean_recipients(recipients: Iterable[str]) -> tuple[str, ...]:
    """Validate and normalize the recipient iterable into a tuple."""
    if isinstance(recipients, str):
        raise ValueError("to recipients must be provided as an iterable of strings")

    clean_recipients = tuple(
        _require_non_blank(recipient, "recipients") for recipient in recipients
    )
    if not clean_recipients:
        raise ValueError("at least one to recipient is required")
    return clean_recipients


def _response_status_code(response: Any) -> int:
    """Read an integer HTTP status code from a response-like object."""
    status_code = getattr(response, "status_code", None)
    if not isinstance(status_code, int):
        raise EmailSendError("HTTP response did not include a status_code")
    return status_code


def _response_json(response: Any) -> dict[str, Any]:
    """Read a JSON object from a response-like object."""
    try:
        body = response.json()
    except Exception as exc:
        raise EmailSendError("OAuth token response was not valid JSON") from exc

    if not isinstance(body, dict):
        raise EmailSendError("OAuth token response was not a JSON object")
    return body


__all__ = [
    "ConsoleEmailSender",
    "EmailMessage",
    "EmailSendError",
    "GraphEmailSender",
    "GraphEmailSettings",
]
