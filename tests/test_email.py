import configparser
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses
from io import StringIO
from pathlib import Path

import pytest

from shamir_app_core import (
    ConsoleEmailSender,
    EmailConfigError,
    EmailMessage,
    EmailSender,
    EmailSendError,
    load_pickup_directory_email_settings,
    PickupDirectoryEmailSender,
    PickupDirectoryEmailSettings,
)


def send_with_sender(sender: EmailSender, message: EmailMessage) -> None:
    sender.send(message)


def make_config(values, section="email"):
    config = configparser.ConfigParser()
    config[section] = values
    return config


def test_email_message_accepts_required_text_fields():
    message = EmailMessage(
        to=["user@example.com"],
        subject="Status update",
        body_text="The job completed.",
    )

    assert message.to == ("user@example.com",)
    assert message.subject == "Status update"
    assert message.body_text == "The job completed."
    assert message.body_html is None


def test_email_message_accepts_optional_html_body():
    message = EmailMessage(
        to=["user@example.com"],
        subject="Status update",
        body_text="The job completed.",
        body_html="<p>The job completed.</p>",
    )

    assert message.body_text == "The job completed."
    assert message.body_html == "<p>The job completed.</p>"


def test_email_message_strips_subject_and_recipients():
    message = EmailMessage(
        to=[" user@example.com ", " other@example.com "],
        subject="  Status update  ",
        body_text="Body text",
    )

    assert message.to == ("user@example.com", "other@example.com")
    assert message.subject == "Status update"


@pytest.mark.parametrize("subject", ["", "   "])
def test_email_message_rejects_blank_subject(subject):
    with pytest.raises(ValueError, match="subject must not be blank"):
        EmailMessage(
            to=["user@example.com"],
            subject=subject,
            body_text="Body text",
        )


@pytest.mark.parametrize("body_text", ["", "   "])
def test_email_message_rejects_blank_body_text(body_text):
    with pytest.raises(ValueError, match="body_text must not be blank"):
        EmailMessage(
            to=["user@example.com"],
            subject="Subject",
            body_text=body_text,
        )


@pytest.mark.parametrize("body_html", ["", "   "])
def test_email_message_rejects_blank_body_html_when_provided(body_html):
    with pytest.raises(ValueError, match="body_html must not be blank"):
        EmailMessage(
            to=["user@example.com"],
            subject="Subject",
            body_text="Body text",
            body_html=body_html,
        )


def test_email_message_rejects_missing_to_recipients():
    with pytest.raises(ValueError, match="at least one to recipient is required"):
        EmailMessage(
            to=[],
            subject="Subject",
            body_text="Body text",
        )


def test_email_message_rejects_plain_string_to_recipients():
    with pytest.raises(ValueError, match="to recipients must be provided"):
        EmailMessage(
            to="user@example.com",
            subject="Subject",
            body_text="Body text",
        )


@pytest.mark.parametrize("recipient", ["", "   "])
def test_email_message_rejects_blank_recipient(recipient):
    with pytest.raises(ValueError, match="recipients must not be blank"):
        EmailMessage(
            to=["user@example.com", recipient],
            subject="Subject",
            body_text="Body text",
        )


def test_console_email_sender_writes_readable_preview():
    stream = StringIO()
    sender = ConsoleEmailSender(stream)
    message = EmailMessage(
        to=["first@example.com", "second@example.com"],
        subject="Status update",
        body_text="The job completed.",
    )

    sender.send(message)

    assert stream.getvalue() == "\n".join(
        [
            "--- Email preview ---",
            "To: first@example.com, second@example.com",
            "Subject: Status update",
            "",
            "The job completed.",
            "--- End email preview ---",
            "",
        ]
    )


def test_console_email_sender_indicates_html_body_without_dumping_html():
    stream = StringIO()
    sender = ConsoleEmailSender(stream)
    message = EmailMessage(
        to=["user@example.com"],
        subject="Status update",
        body_text="The job completed.",
        body_html="<p>The job <strong>completed</strong>.</p>",
    )

    sender.send(message)

    preview = stream.getvalue()
    assert "[HTML body attached]" in preview
    assert "<strong>completed</strong>" not in preview


def test_email_sender_protocol_accepts_console_email_sender_structurally():
    stream = StringIO()
    sender = ConsoleEmailSender(stream)
    message = EmailMessage(
        to=["user@example.com"],
        subject="Status update",
        body_text="The job completed.",
    )

    send_with_sender(sender, message)

    assert "Subject: Status update" in stream.getvalue()


def test_pickup_directory_email_sender_writes_one_parseable_eml_file(tmp_path):
    sender = PickupDirectoryEmailSender(
        PickupDirectoryEmailSettings(
            pickup_dir=tmp_path,
            sender="sender@example.com",
        )
    )
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Status update",
        body_text="The job completed.",
    )

    sender.send(message)

    files = list(tmp_path.glob("*.eml"))
    assert len(files) == 1

    parsed = BytesParser(policy=policy.default).parsebytes(files[0].read_bytes())
    assert parsed["From"] == "sender@example.com"
    assert parsed["To"] == "recipient@example.com"
    assert parsed["Subject"] == "Status update"
    assert parsed.get_content_type() == "text/plain"
    assert not parsed.is_multipart()
    assert parsed.get_body(preferencelist=("plain",)).get_content().splitlines() == [
        "The job completed."
    ]


def test_pickup_directory_email_sender_plain_text_uses_smtp_crlf_output(tmp_path):
    sender = PickupDirectoryEmailSender(
        PickupDirectoryEmailSettings(
            pickup_dir=tmp_path,
            sender="sender@example.com",
        )
    )
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Status update",
        body_text="The job completed.",
    )

    sender.send(message)

    output = next(tmp_path.glob("*.eml")).read_bytes()
    assert b"\r\n" in output
    assert b"\n" not in output.replace(b"\r\n", b"")


def test_pickup_directory_email_sender_writes_html_as_multipart_alternative(tmp_path):
    sender = PickupDirectoryEmailSender(
        PickupDirectoryEmailSettings(
            pickup_dir=tmp_path,
            sender="sender@example.com",
        )
    )
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Status update",
        body_text="The job completed.",
        body_html="<p>The job <strong>completed</strong>.</p>",
    )

    sender.send(message)

    output = next(tmp_path.glob("*.eml")).read_bytes()
    assert b"\r\n" in output
    assert b"\n" not in output.replace(b"\r\n", b"")

    parsed = BytesParser(policy=policy.default).parsebytes(output)
    assert parsed.get_content_type() == "multipart/alternative"
    assert parsed.is_multipart()

    plain_body = parsed.get_body(preferencelist=("plain",))
    html_body = parsed.get_body(preferencelist=("html",))
    assert plain_body is not None
    assert html_body is not None
    assert plain_body.get_content_type() == "text/plain"
    assert html_body.get_content_type() == "text/html"
    assert plain_body.get_content().splitlines() == ["The job completed."]
    assert html_body.get_content().splitlines() == [
        "<p>The job <strong>completed</strong>.</p>"
    ]


def test_load_pickup_directory_email_settings_loads_pickup_dir_and_sender():
    config = make_config(
        {
            "pickup_dir": "sample-pickup",
            "sender": "sender@example.com",
        }
    )

    settings = load_pickup_directory_email_settings(config)

    assert settings == PickupDirectoryEmailSettings(
        pickup_dir=Path("sample-pickup"),
        sender="sender@example.com",
    )


def test_load_pickup_directory_email_settings_supports_pickup_backend():
    config = make_config(
        {
            "backend": "pickup",
            "pickup_dir": "sample-pickup",
            "sender": "sender@example.com",
        }
    )

    settings = load_pickup_directory_email_settings(config)

    assert isinstance(settings, PickupDirectoryEmailSettings)


def test_load_pickup_directory_email_settings_allows_missing_backend():
    config = make_config(
        {
            "pickup_dir": "sample-pickup",
            "sender": "sender@example.com",
        }
    )

    settings = load_pickup_directory_email_settings(config)

    assert settings.sender == "sender@example.com"


def test_load_pickup_directory_email_settings_rejects_graph_backend():
    config = make_config(
        {
            "backend": "graph",
            "pickup_dir": "sample-pickup",
            "sender": "sender@example.com",
        }
    )

    with pytest.raises(EmailConfigError, match="only supports .* pickup backend"):
        load_pickup_directory_email_settings(config)


def test_load_pickup_directory_email_settings_rejects_unsupported_backend():
    config = make_config(
        {
            "backend": "smtp_relay",
            "pickup_dir": "sample-pickup",
            "sender": "sender@example.com",
        }
    )

    with pytest.raises(EmailConfigError, match="only supports .* pickup backend"):
        load_pickup_directory_email_settings(config)


def test_load_pickup_directory_email_settings_missing_section_raises_config_error():
    config = configparser.ConfigParser()

    with pytest.raises(EmailConfigError, match="Required config section email is missing"):
        load_pickup_directory_email_settings(config)


@pytest.mark.parametrize("option", ["pickup_dir", "sender"])
def test_load_pickup_directory_email_settings_missing_required_value_raises_config_error(
    option,
):
    values = {
        "pickup_dir": "sample-pickup",
        "sender": "sender@example.com",
    }
    del values[option]
    config = make_config(values)

    with pytest.raises(EmailConfigError, match=option):
        load_pickup_directory_email_settings(config)


@pytest.mark.parametrize("option", ["pickup_dir", "sender"])
def test_load_pickup_directory_email_settings_blank_required_value_raises_config_error(
    option,
):
    values = {
        "pickup_dir": "sample-pickup",
        "sender": "sender@example.com",
    }
    values[option] = "   "
    config = make_config(values)

    with pytest.raises(EmailConfigError, match=option):
        load_pickup_directory_email_settings(config)


def test_pickup_directory_email_sender_handles_multiple_recipients(tmp_path):
    sender = PickupDirectoryEmailSender(
        PickupDirectoryEmailSettings(
            pickup_dir=tmp_path,
            sender="sender@example.com",
        )
    )
    message = EmailMessage(
        to=["first@example.com", "second@example.com"],
        subject="Status update",
        body_text="The job completed.",
    )

    sender.send(message)

    files = list(tmp_path.glob("*.eml"))
    parsed = BytesParser(policy=policy.default).parsebytes(files[0].read_bytes())

    assert getaddresses(parsed.get_all("To", [])) == [
        ("", "first@example.com"),
        ("", "second@example.com"),
    ]


def test_pickup_directory_email_sender_uses_unique_filenames(tmp_path):
    sender = PickupDirectoryEmailSender(
        PickupDirectoryEmailSettings(
            pickup_dir=tmp_path,
            sender="sender@example.com",
        )
    )
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Status update",
        body_text="The job completed.",
    )

    sender.send(message)
    sender.send(message)

    files = list(tmp_path.glob("*.eml"))
    assert len(files) == 2
    assert len({path.name for path in files}) == 2


def test_pickup_directory_email_sender_missing_directory_raises_email_send_error(
    tmp_path,
):
    missing_pickup_dir = tmp_path / "missing-pickup"
    sender = PickupDirectoryEmailSender(
        PickupDirectoryEmailSettings(
            pickup_dir=missing_pickup_dir,
            sender="sender@example.com",
        )
    )
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Status update",
        body_text="The job completed.",
    )

    with pytest.raises(EmailSendError, match="Pickup directory does not exist"):
        sender.send(message)

    assert not missing_pickup_dir.exists()


def test_pickup_directory_email_sender_header_failure_creates_no_eml_file(tmp_path):
    sender = PickupDirectoryEmailSender(
        PickupDirectoryEmailSettings(
            pickup_dir=tmp_path,
            sender="sender@example.com",
        )
    )
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Bad\nSubject",
        body_text="The job completed.",
    )

    with pytest.raises(ValueError, match="Header values may not contain"):
        sender.send(message)

    assert list(tmp_path.glob("*.eml")) == []


def test_pickup_directory_email_sender_keeps_test_files_in_tmp_path(tmp_path):
    sender = PickupDirectoryEmailSender(
        PickupDirectoryEmailSettings(
            pickup_dir=tmp_path,
            sender="sender@example.com",
        )
    )
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Status update",
        body_text="The job completed.",
    )

    sender.send(message)

    files = list(tmp_path.glob("*.eml"))
    assert len(files) == 1
    assert files[0].is_relative_to(tmp_path)
    assert "SHAV01" not in str(files[0])
    assert "Pickup" not in str(files[0])


def test_email_sender_protocol_accepts_pickup_directory_email_sender_structurally(
    tmp_path,
):
    sender = PickupDirectoryEmailSender(
        PickupDirectoryEmailSettings(
            pickup_dir=tmp_path,
            sender="sender@example.com",
        )
    )
    message = EmailMessage(
        to=["recipient@example.com"],
        subject="Status update",
        body_text="The job completed.",
    )

    send_with_sender(sender, message)

    assert len(list(tmp_path.glob("*.eml"))) == 1


def test_email_api_is_available_from_top_level_package():
    assert EmailMessage.__name__ == "EmailMessage"
    assert EmailSender.__name__ == "EmailSender"
    assert ConsoleEmailSender.__name__ == "ConsoleEmailSender"
    assert (
        load_pickup_directory_email_settings.__name__
        == "load_pickup_directory_email_settings"
    )
    assert PickupDirectoryEmailSettings.__name__ == "PickupDirectoryEmailSettings"
    assert PickupDirectoryEmailSender.__name__ == "PickupDirectoryEmailSender"
