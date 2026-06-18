import configparser
from dataclasses import dataclass
from io import BytesIO
from urllib.error import HTTPError

import pytest

from shamir_app_core import (
    EmailConfigError,
    EmailMessage,
    EmailSender,
    EmailSendError,
    GraphEmailSender,
    GraphEmailSettings,
    load_graph_email_settings,
    UrlLibHttpResponse,
    UrlLibHttpTransport,
)


def send_with_sender(sender: EmailSender, message: EmailMessage) -> None:
    sender.send(message)


@dataclass
class FakeResponse:
    status_code: int
    json_body: dict | None = None

    def json(self):
        if self.json_body is None:
            raise ValueError("response has no JSON body")
        return self.json_body


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def post(self, url, *, data=None, json=None, headers=None, timeout_seconds):
        self.requests.append(
            {
                "url": url,
                "data": data,
                "json": json,
                "headers": headers,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.responses.pop(0)


class RaisingTransport:
    def __init__(self, responses_before_error=None):
        self.responses_before_error = list(responses_before_error or [])

    def post(self, url, *, data=None, json=None, headers=None, timeout_seconds):
        if self.responses_before_error:
            return self.responses_before_error.pop(0)
        raise TimeoutError("request timed out")


class FakeUrlOpenResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None

    def getcode(self):
        return self.status_code

    def read(self):
        return self.body


class RecordingUrlOpen:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def __call__(self, request, *, timeout):
        self.requests.append({"request": request, "timeout": timeout})
        return self.response


def make_settings(**overrides):
    values = {
        "tenant_id": "tenant-id",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "sender": "sender@example.com",
    }
    values.update(overrides)
    return GraphEmailSettings(**values)


def test_graph_email_settings_repr_does_not_include_client_secret():
    settings = make_settings(client_secret="very-sensitive-secret")

    settings_repr = repr(settings)

    assert "very-sensitive-secret" not in settings_repr
    assert "client_secret" not in settings_repr


def make_message():
    return EmailMessage(
        to=["first@example.com", "second@example.com"],
        subject="Status update",
        body_text="The job completed.",
    )


def make_html_message():
    return EmailMessage(
        to=["first@example.com", "second@example.com"],
        subject="Status update",
        body_text="The job completed.",
        body_html="<p>The job <strong>completed</strong>.</p>",
    )


def make_config(values, section="email"):
    config = configparser.ConfigParser()
    config[section] = values
    return config


def test_load_graph_email_settings_with_direct_client_secret():
    config = make_config(
        {
            "tenant_id": "tenant-id",
            "client_id": "client-id",
            "client_secret": "client-secret",
            "sender": "sender@example.com",
        }
    )

    settings = load_graph_email_settings(config)

    assert settings == GraphEmailSettings(
        tenant_id="tenant-id",
        client_id="client-id",
        client_secret="client-secret",
        sender="sender@example.com",
    )


def test_load_graph_email_settings_with_client_secret_env():
    config = make_config(
        {
            "tenant_id": "tenant-id",
            "client_id": "client-id",
            "client_secret_env": "EMAIL_CLIENT_SECRET",
            "sender": "sender@example.com",
        }
    )

    settings = load_graph_email_settings(
        config,
        environ={"EMAIL_CLIENT_SECRET": "secret-from-env"},
    )

    assert settings.client_secret == "secret-from-env"


def test_load_graph_email_settings_missing_required_field_raises_email_config_error():
    config = make_config(
        {
            "client_id": "client-id",
            "client_secret": "client-secret",
            "sender": "sender@example.com",
        }
    )

    with pytest.raises(EmailConfigError, match="tenant_id"):
        load_graph_email_settings(config)


def test_load_graph_email_settings_re_raises_email_config_error_unchanged():
    config = make_config(
        {
            "client_id": "client-id",
            "client_secret": "client-secret",
            "sender": "sender@example.com",
        }
    )

    with pytest.raises(EmailConfigError) as exc_info:
        load_graph_email_settings(config)

    assert str(exc_info.value) == "Required config option tenant_id in section email is missing"
    assert exc_info.value.__cause__ is None


def test_load_graph_email_settings_missing_section_raises_email_config_error():
    config = configparser.ConfigParser()

    with pytest.raises(EmailConfigError, match="Required config section email is missing"):
        load_graph_email_settings(config)


def test_load_graph_email_settings_rejects_both_client_secret_sources():
    config = make_config(
        {
            "tenant_id": "tenant-id",
            "client_id": "client-id",
            "client_secret": "client-secret",
            "client_secret_env": "EMAIL_CLIENT_SECRET",
            "sender": "sender@example.com",
        }
    )

    with pytest.raises(EmailConfigError, match="mutually exclusive"):
        load_graph_email_settings(config)


def test_load_graph_email_settings_rejects_missing_client_secret_env_value():
    config = make_config(
        {
            "tenant_id": "tenant-id",
            "client_id": "client-id",
            "client_secret_env": "EMAIL_CLIENT_SECRET",
            "sender": "sender@example.com",
        }
    )

    with pytest.raises(EmailConfigError, match="missing or blank"):
        load_graph_email_settings(config, environ={})


def test_load_graph_email_settings_allows_graph_backend():
    config = make_config(
        {
            "backend": "graph",
            "tenant_id": "tenant-id",
            "client_id": "client-id",
            "client_secret": "client-secret",
            "sender": "sender@example.com",
        }
    )

    settings = load_graph_email_settings(config)

    assert settings.sender == "sender@example.com"


def test_load_graph_email_settings_rejects_unsupported_backend():
    config = make_config(
        {
            "backend": "smtp_relay",
            "tenant_id": "tenant-id",
            "client_id": "client-id",
            "client_secret": "client-secret",
            "sender": "sender@example.com",
        }
    )

    with pytest.raises(EmailConfigError, match="only supports the Graph backend"):
        load_graph_email_settings(config)


def test_load_graph_email_settings_parses_optional_values():
    config = make_config(
        {
            "tenant_id": "tenant-id",
            "client_id": "client-id",
            "client_secret": "client-secret",
            "sender": "sender@example.com",
            "timeout_seconds": "45",
            "save_to_sent_items": "false",
            "authority_host": "https://login.example.test/",
            "graph_host": "https://graph.example.test/",
        }
    )

    settings = load_graph_email_settings(config)

    assert settings.timeout_seconds == 45.0
    assert settings.save_to_sent_items is False
    assert settings.authority_host == "https://login.example.test"
    assert settings.graph_host == "https://graph.example.test"


def test_load_graph_email_settings_parses_decimal_timeout_seconds():
    config = make_config(
        {
            "tenant_id": "tenant-id",
            "client_id": "client-id",
            "client_secret": "client-secret",
            "sender": "sender@example.com",
            "timeout_seconds": "12.5",
        }
    )

    settings = load_graph_email_settings(config)

    assert settings.timeout_seconds == 12.5


def test_graph_email_sender_requests_token_and_sends_mail_payload():
    transport = FakeTransport(
        [
            FakeResponse(200, {"access_token": "token-value"}),
            FakeResponse(202),
        ]
    )
    sender = GraphEmailSender(make_settings(timeout_seconds=12.5), transport)

    sender.send(make_message())

    token_request = transport.requests[0]
    assert token_request == {
        "url": "https://login.microsoftonline.com/tenant-id/oauth2/v2.0/token",
        "data": {
            "client_id": "client-id",
            "client_secret": "client-secret",
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
        },
        "json": None,
        "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        "timeout_seconds": 12.5,
    }

    send_request = transport.requests[1]
    assert send_request["url"] == (
        "https://graph.microsoft.com/v1.0/users/sender%40example.com/sendMail"
    )
    assert send_request["headers"] == {
        "Authorization": "Bearer token-value",
        "Content-Type": "application/json",
    }
    assert send_request["timeout_seconds"] == 12.5
    assert send_request["json"] == {
        "message": {
            "subject": "Status update",
            "body": {
                "contentType": "Text",
                "content": "The job completed.",
            },
            "toRecipients": [
                {"emailAddress": {"address": "first@example.com"}},
                {"emailAddress": {"address": "second@example.com"}},
            ],
        },
        "saveToSentItems": True,
    }


def test_graph_email_sender_plain_text_payload_uses_text_content_type():
    transport = FakeTransport(
        [
            FakeResponse(200, {"access_token": "token-value"}),
            FakeResponse(202),
        ]
    )
    sender = GraphEmailSender(make_settings(), transport)

    sender.send(make_message())

    body = transport.requests[1]["json"]["message"]["body"]
    assert body == {
        "contentType": "Text",
        "content": "The job completed.",
    }


def test_graph_email_sender_html_payload_uses_html_body_content():
    transport = FakeTransport(
        [
            FakeResponse(200, {"access_token": "token-value"}),
            FakeResponse(202),
        ]
    )
    sender = GraphEmailSender(make_settings(), transport)

    sender.send(make_html_message())

    body = transport.requests[1]["json"]["message"]["body"]
    assert body == {
        "contentType": "HTML",
        "content": "<p>The job <strong>completed</strong>.</p>",
    }


def test_graph_email_sender_token_failure_raises_email_send_error():
    transport = FakeTransport([FakeResponse(400, {"error": "invalid_client"})])
    sender = GraphEmailSender(make_settings(), transport)

    with pytest.raises(EmailSendError, match="OAuth token request failed"):
        sender.send(make_message())


def test_graph_email_sender_token_transport_error_raises_email_send_error():
    sender = GraphEmailSender(make_settings(), RaisingTransport())

    with pytest.raises(EmailSendError, match="OAuth token request transport failed") as exc_info:
        sender.send(make_message())

    assert isinstance(exc_info.value.__cause__, TimeoutError)


def test_graph_email_sender_missing_access_token_raises_email_send_error():
    transport = FakeTransport([FakeResponse(200, {"token_type": "Bearer"})])
    sender = GraphEmailSender(make_settings(), transport)

    with pytest.raises(EmailSendError, match="access_token"):
        sender.send(make_message())


def test_graph_email_sender_send_mail_transport_error_raises_email_send_error():
    transport = RaisingTransport([FakeResponse(200, {"access_token": "token-value"})])
    sender = GraphEmailSender(make_settings(), transport)

    with pytest.raises(EmailSendError, match="Graph sendMail request failed") as exc_info:
        sender.send(make_message())

    assert isinstance(exc_info.value.__cause__, TimeoutError)


def test_graph_email_sender_send_mail_non_202_raises_email_send_error():
    transport = FakeTransport(
        [
            FakeResponse(200, {"access_token": "token-value"}),
            FakeResponse(400, {"error": "bad_request"}),
        ]
    )
    sender = GraphEmailSender(make_settings(), transport)

    with pytest.raises(EmailSendError, match="Graph sendMail failed"):
        sender.send(make_message())


def test_graph_email_sender_includes_save_to_sent_items_false_in_payload():
    transport = FakeTransport(
        [
            FakeResponse(200, {"access_token": "token-value"}),
            FakeResponse(202),
        ]
    )
    sender = GraphEmailSender(make_settings(save_to_sent_items=False), transport)

    sender.send(make_message())

    assert transport.requests[1]["json"]["saveToSentItems"] is False


def test_email_sender_protocol_accepts_graph_email_sender_structurally():
    transport = FakeTransport(
        [
            FakeResponse(200, {"access_token": "token-value"}),
            FakeResponse(202),
        ]
    )
    sender = GraphEmailSender(make_settings(), transport)

    send_with_sender(sender, make_message())

    assert len(transport.requests) == 2


def test_graph_email_api_is_available_from_top_level_package():
    assert GraphEmailSettings.__name__ == "GraphEmailSettings"
    assert GraphEmailSender.__name__ == "GraphEmailSender"
    assert EmailSendError.__name__ == "EmailSendError"


def test_url_lib_http_transport_encodes_form_post_data():
    urlopen = RecordingUrlOpen(FakeUrlOpenResponse(200, b'{"ok": true}'))
    transport = UrlLibHttpTransport(urlopen=urlopen)

    response = transport.post(
        "https://example.invalid/token",
        data={"client_id": "client-id", "scope": "https://graph.microsoft.com/.default"},
        timeout_seconds=7,
    )

    recorded = urlopen.requests[0]
    request = recorded["request"]
    assert request.full_url == "https://example.invalid/token"
    assert request.get_method() == "POST"
    assert request.data == (
        b"client_id=client-id&scope=https%3A%2F%2Fgraph.microsoft.com%2F.default"
    )
    assert request.get_header("Content-type") == "application/x-www-form-urlencoded"
    assert recorded["timeout"] == 7
    assert response.status_code == 200


def test_url_lib_http_transport_encodes_json_post_data():
    urlopen = RecordingUrlOpen(FakeUrlOpenResponse(202, b""))
    transport = UrlLibHttpTransport(urlopen=urlopen)

    transport.post(
        "https://example.invalid/sendMail",
        json={"message": {"subject": "Status update"}},
        timeout_seconds=3,
    )

    request = urlopen.requests[0]["request"]
    assert request.get_header("Content-type") == "application/json"
    assert request.data == b'{"message": {"subject": "Status update"}}'


def test_url_lib_http_transport_forwards_headers():
    urlopen = RecordingUrlOpen(FakeUrlOpenResponse(202, b""))
    transport = UrlLibHttpTransport(urlopen=urlopen)

    transport.post(
        "https://example.invalid/sendMail",
        json={"message": {}},
        headers={"Authorization": "Bearer token-value", "Content-Type": "application/json"},
        timeout_seconds=3,
    )

    request = urlopen.requests[0]["request"]
    assert request.get_header("Authorization") == "Bearer token-value"
    assert request.get_header("Content-type") == "application/json"


def test_url_lib_http_transport_returns_response_for_http_error():
    body = b'{"error": "invalid_client"}'

    def raise_http_error(request, *, timeout):
        raise HTTPError(
            request.full_url,
            400,
            "Bad Request",
            hdrs={},
            fp=BytesIO(body),
        )

    transport = UrlLibHttpTransport(urlopen=raise_http_error)

    response = transport.post(
        "https://example.invalid/token",
        data={"client_id": "client-id"},
        timeout_seconds=3,
    )

    assert response.status_code == 400
    assert response.body == body
    assert response.text == '{"error": "invalid_client"}'
    assert response.json() == {"error": "invalid_client"}


def test_url_lib_http_response_repr_does_not_include_body_or_token_value():
    response = UrlLibHttpResponse(
        status_code=200,
        body=b'{"access_token": "secret-token-value"}',
    )

    response_repr = repr(response)

    assert "body" not in response_repr
    assert "secret-token-value" not in response_repr


def test_url_lib_http_response_json_parses_json_object():
    response = UrlLibHttpResponse(status_code=200, body=b'{"access_token": "token"}')

    assert response.json() == {"access_token": "token"}


def test_url_lib_http_response_json_raises_for_invalid_json():
    response = UrlLibHttpResponse(status_code=200, body=b"not json")

    with pytest.raises(ValueError):
        response.json()
