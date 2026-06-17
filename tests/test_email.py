from io import StringIO

import pytest

from shamir_app_core import ConsoleEmailSender, EmailMessage


def test_email_message_accepts_required_text_fields():
    message = EmailMessage(
        to=["user@example.com"],
        subject="Status update",
        body_text="The job completed.",
    )

    assert message.to == ("user@example.com",)
    assert message.subject == "Status update"
    assert message.body_text == "The job completed."


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


def test_email_api_is_available_from_top_level_package():
    assert EmailMessage.__name__ == "EmailMessage"
    assert ConsoleEmailSender.__name__ == "ConsoleEmailSender"
