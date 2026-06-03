import pytest

from shamir_app_core.errors import ApplicationInitError, FatalError, RuntimeError


@pytest.mark.parametrize(
    "error_class",
    [
        ApplicationInitError,
        FatalError,
        RuntimeError,
    ],
)
def test_exception_string_behavior(error_class):
    message = "legacy message"

    error = error_class(message)

    assert error.value == message
    assert str(error) == message
