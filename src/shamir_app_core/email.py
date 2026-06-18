"""Generic text email messages and sender foundations."""

from datetime import datetime, timezone
from email.generator import BytesGenerator
from email.message import EmailMessage as StdlibEmailMessage
from email import policy
from io import BytesIO
import json as json_module
import os
from pathlib import Path
import urllib.error
import urllib.request
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol, TextIO
from urllib.parse import quote, urlencode
from uuid import uuid4


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


class EmailSender(Protocol):
    """Backend-agnostic protocol for sending validated email messages."""

    def send(self, message: EmailMessage) -> None:
        """Send the provided email message."""


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


class EmailConfigError(ValueError):
    """Raised when email settings cannot be loaded from configuration."""


@dataclass(frozen=True)
class PickupDirectoryEmailSettings:
    """Settings for writing MIME messages into an SMTP pickup directory."""

    pickup_dir: Path | str
    sender: str
    filename_prefix: str = "email"
    file_extension: str = ".eml"

    def __post_init__(self) -> None:
        """Normalize path and text settings."""
        object.__setattr__(self, "pickup_dir", Path(self.pickup_dir))
        object.__setattr__(self, "sender", _require_non_blank(self.sender, "sender"))
        object.__setattr__(
            self,
            "filename_prefix",
            _require_non_blank(self.filename_prefix, "filename_prefix"),
        )
        object.__setattr__(
            self,
            "file_extension",
            _require_non_blank(self.file_extension, "file_extension"),
        )


class PickupDirectoryEmailSender:
    """Write MIME .eml files directly into an SMTP pickup directory."""

    def __init__(self, settings: PickupDirectoryEmailSettings) -> None:
        """Create a pickup-directory sender with explicit settings."""
        self.settings = settings

    def send(self, message: EmailMessage) -> None:
        """Write the message as a unique binary MIME file in the pickup directory."""
        pickup_dir = self.settings.pickup_dir
        if not pickup_dir.is_dir():
            raise EmailSendError(f"Pickup directory does not exist: {pickup_dir}")

        message_bytes = self._build_message_bytes(message)
        path = pickup_dir / self._make_filename()
        try:
            with path.open("xb") as handle:
                handle.write(message_bytes)
        except OSError as exc:
            raise EmailSendError(f"Could not write pickup email file: {path}") from exc

    def _make_filename(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        return (
            f"{self.settings.filename_prefix}-{timestamp}-{uuid4().hex}"
            f"{self.settings.file_extension}"
        )

    def _build_message_bytes(self, message: EmailMessage) -> bytes:
        mime_message = StdlibEmailMessage(policy=policy.SMTP)
        mime_message["From"] = self.settings.sender
        mime_message["To"] = ", ".join(message.to)
        mime_message["Subject"] = message.subject
        mime_message.set_content(message.body_text)

        output = BytesIO()
        generator = BytesGenerator(output, policy=policy.SMTP)
        generator.flatten(mime_message)
        return output.getvalue()


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


@dataclass(frozen=True)
class UrlLibHttpResponse:
    """Small response wrapper returned by UrlLibHttpTransport."""

    status_code: int
    body: bytes = field(repr=False)

    @property
    def text(self) -> str:
        """Decode the response body as UTF-8 text for inspection."""
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        """Parse the response body as JSON."""
        return json_module.loads(self.text)


class UrlLibHttpTransport:
    """HTTP POST transport implemented with urllib.request."""

    def __init__(self, urlopen=None) -> None:
        """Create a transport, optionally injecting urlopen for tests."""
        self.urlopen = urlopen or urllib.request.urlopen

    def post(
        self,
        url: str,
        *,
        data: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: float,
    ) -> UrlLibHttpResponse:
        """Send a form or JSON POST request and return a response wrapper."""
        body, request_headers = self._prepare_request_body_and_headers(
            data=data,
            json=json,
            headers=headers,
        )
        request = urllib.request.Request(
            url,
            data=body,
            headers=request_headers,
            method="POST",
        )

        try:
            response = self.urlopen(request, timeout=timeout_seconds)
        except urllib.error.HTTPError as exc:
            return UrlLibHttpResponse(status_code=exc.code, body=exc.read())

        with response:
            return UrlLibHttpResponse(
                status_code=response.getcode(),
                body=response.read(),
            )

    def _prepare_request_body_and_headers(
        self,
        *,
        data: dict[str, str] | None,
        json: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> tuple[bytes | None, dict[str, str]]:
        """Encode the request body and apply a default content type."""
        if data is not None and json is not None:
            raise ValueError("data and json cannot both be provided")

        request_headers = dict(headers or {})
        if data is not None:
            body = urlencode(data).encode("utf-8")
            _set_default_header(
                request_headers,
                "Content-Type",
                "application/x-www-form-urlencoded",
            )
            return body, request_headers

        if json is not None:
            body = json_module.dumps(json).encode("utf-8")
            _set_default_header(request_headers, "Content-Type", "application/json")
            return body, request_headers

        return None, request_headers


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


def load_graph_email_settings(
    config: Any,
    section: str = "email",
    environ: Mapping[str, str] | None = None,
) -> GraphEmailSettings:
    """Load Graph email settings from a config-like object."""
    if not _config_has_section(config, section):
        raise EmailConfigError(f"Required config section {section} is missing")

    backend = _read_optional_config_string(config, section, "backend")
    if backend is not None and backend.lower() != "graph":
        raise EmailConfigError(
            "load_graph_email_settings only supports the Graph backend; "
            f"got {backend!r}"
        )

    secret = _load_graph_client_secret(config, section, environ=environ)
    try:
        return GraphEmailSettings(
            tenant_id=_read_required_config_string(config, section, "tenant_id"),
            client_id=_read_required_config_string(config, section, "client_id"),
            client_secret=secret,
            sender=_read_required_config_string(config, section, "sender"),
            timeout_seconds=_read_optional_config_float(
                config,
                section,
                "timeout_seconds",
                GraphEmailSettings.timeout_seconds,
            ),
            save_to_sent_items=_read_optional_config_boolean(
                config,
                section,
                "save_to_sent_items",
                GraphEmailSettings.save_to_sent_items,
            ),
            authority_host=_read_config_string_or_default(
                config,
                section,
                "authority_host",
                GraphEmailSettings.authority_host,
            ),
            graph_host=_read_config_string_or_default(
                config,
                section,
                "graph_host",
                GraphEmailSettings.graph_host,
            ),
        )
    except EmailConfigError:
        raise
    except ValueError as exc:
        raise EmailConfigError(str(exc)) from exc


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


def _load_graph_client_secret(
    config: Any,
    section: str,
    *,
    environ: Mapping[str, str] | None,
) -> str:
    has_direct_secret = _config_has_option(config, section, "client_secret")
    has_env_secret = _config_has_option(config, section, "client_secret_env")

    if has_direct_secret and has_env_secret:
        raise EmailConfigError(
            "Config options client_secret and client_secret_env are mutually exclusive"
        )
    if not has_direct_secret and not has_env_secret:
        raise EmailConfigError(
            "Required config option client_secret or client_secret_env is missing"
        )

    if has_direct_secret:
        return _read_required_config_string(config, section, "client_secret")

    env_name = _read_required_config_string(config, section, "client_secret_env")
    env_values = os.environ if environ is None else environ
    secret = env_values.get(env_name)
    if not isinstance(secret, str) or not secret.strip():
        raise EmailConfigError(
            f"Environment variable {env_name!r} for client_secret is missing or blank"
        )
    return secret


def _read_required_config_string(config: Any, section: str, option: str) -> str:
    if not _config_has_option(config, section, option):
        raise EmailConfigError(
            f"Required config option {option} in section {section} is missing"
        )
    value = _config_get(config, section, option)
    if not isinstance(value, str) or not value.strip():
        raise EmailConfigError(
            f"Required config option {option} in section {section} is blank"
        )
    return value.strip()


def _read_optional_config_string(
    config: Any,
    section: str,
    option: str,
    default: str | None = None,
) -> str | None:
    if not _config_has_option(config, section, option):
        return default
    value = _config_get(config, section, option)
    if not isinstance(value, str) or not value.strip():
        return default
    return value.strip()


def _read_config_string_or_default(
    config: Any,
    section: str,
    option: str,
    default: str,
) -> str:
    value = _read_optional_config_string(config, section, option)
    if value is None:
        return default
    return value


def _read_optional_config_float(
    config: Any,
    section: str,
    option: str,
    default: float,
) -> float:
    if not _config_has_option(config, section, option):
        return default
    try:
        return float(_config_get(config, section, option))
    except ValueError as exc:
        raise EmailConfigError(
            f"Config option {option} in section {section} must be a number"
        ) from exc


def _read_optional_config_boolean(
    config: Any,
    section: str,
    option: str,
    default: bool,
) -> bool:
    if not _config_has_option(config, section, option):
        return default
    value = _config_get(config, section, option).strip().lower()
    if value in {"1", "yes", "true", "on"}:
        return True
    if value in {"0", "no", "false", "off"}:
        return False
    raise EmailConfigError(
        f"Config option {option} in section {section} must be a boolean"
    )


def _config_has_option(config: Any, section: str, option: str) -> bool:
    try:
        return bool(config.has_option(section, option))
    except AttributeError:
        return option in config[section]


def _config_has_section(config: Any, section: str) -> bool:
    if hasattr(config, "has_section"):
        return bool(config.has_section(section))
    if hasattr(config, "sections"):
        return section in config.sections()
    try:
        config[section]
    except KeyError:
        return False
    return True


def _config_get(config: Any, section: str, option: str) -> str:
    try:
        return config.get(section, option)
    except AttributeError:
        return config[section][option]


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


def _set_default_header(
    headers: dict[str, str],
    name: str,
    value: str,
) -> None:
    """Set a header only when it is not already present case-insensitively."""
    if not any(existing.lower() == name.lower() for existing in headers):
        headers[name] = value


__all__ = [
    "ConsoleEmailSender",
    "EmailConfigError",
    "EmailMessage",
    "EmailSender",
    "EmailSendError",
    "GraphEmailSender",
    "GraphEmailSettings",
    "load_graph_email_settings",
    "PickupDirectoryEmailSender",
    "PickupDirectoryEmailSettings",
    "UrlLibHttpResponse",
    "UrlLibHttpTransport",
]
