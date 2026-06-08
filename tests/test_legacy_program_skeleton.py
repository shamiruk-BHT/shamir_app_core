import importlib.util
from pathlib import Path

import pytest


SKELETON_PATH = (
    Path(__file__).resolve().parents[1] / "examples" / "legacy_program_skeleton.py"
)
SKELETON_SPEC = importlib.util.spec_from_file_location(
    "legacy_program_skeleton", SKELETON_PATH
)
skeleton = importlib.util.module_from_spec(SKELETON_SPEC)
SKELETON_SPEC.loader.exec_module(skeleton)


class FakeConnection:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeLogger:
    def __init__(self):
        self.info_messages = []
        self.warning_messages = []
        self.exception_messages = []

    def info(self, message):
        self.info_messages.append(message)

    def warning(self, message):
        self.warning_messages.append(message)

    def exception(self, message):
        self.exception_messages.append(message)


@pytest.fixture(autouse=True)
def runtime_identity(monkeypatch):
    monkeypatch.setenv("USERNAME", "test-user")
    monkeypatch.setenv("COMPUTERNAME", "test-machine")


def write_fake_ini(tmp_path):
    ini_path = tmp_path / "shamiruk.ini"
    ini_path.write_text(
        "\n".join(
            [
                "[legacy_program_skeleton]",
                "Name = example",
                "",
                "[mysql]",
                "host = localhost",
                "user = fake-user",
                "password = fake-password",
                "database = fake-db",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return ini_path


def patch_logger(monkeypatch):
    logger = FakeLogger()
    calls = []

    def fake_create_logger(name, log_dir, **kwargs):
        calls.append(
            {
                "name": name,
                "log_dir": log_dir,
                "console": kwargs.get("console"),
            }
        )
        return logger

    monkeypatch.setattr(skeleton, "create_logger", fake_create_logger)
    return calls, logger


def patch_successful_db(monkeypatch):
    connection = FakeConnection()
    calls = []

    def fake_create_mysql_connection(config):
        calls.append(config)
        return connection

    monkeypatch.setattr(skeleton, "create_mysql_connection", fake_create_mysql_connection)
    return calls, connection


def patch_successful_program_logic(monkeypatch):
    calls = []

    def fake_run_program_logic(config, connection, log):
        calls.append(
            {
                "config": config,
                "connection": connection,
                "log": log,
            }
        )
        return 0

    monkeypatch.setattr(skeleton, "run_program_logic", fake_run_program_logic)
    return calls


def test_parse_args_requires_ini():
    with pytest.raises(SystemExit):
        skeleton.parse_args([])


def test_parse_args_supports_no_console(tmp_path):
    ini_path = tmp_path / "shamiruk.ini"

    args = skeleton.parse_args(["--ini", str(ini_path), "--no-console"])

    assert args.ini == str(ini_path)
    assert args.no_console is True


def test_main_no_console_does_not_print_banner(tmp_path, monkeypatch):
    ini_path = write_fake_ini(tmp_path)
    patch_logger(monkeypatch)
    patch_successful_db(monkeypatch)
    patch_successful_program_logic(monkeypatch)
    banner_calls = []
    monkeypatch.setattr(skeleton, "print_banner", lambda *args, **kwargs: banner_calls.append(args))

    result = skeleton.main(["--ini", str(ini_path), "--no-console"])

    assert result == 0
    assert banner_calls == []


def test_main_no_console_skips_confirm_proceed(tmp_path, monkeypatch):
    ini_path = write_fake_ini(tmp_path)
    patch_logger(monkeypatch)
    patch_successful_db(monkeypatch)
    patch_successful_program_logic(monkeypatch)
    monkeypatch.setattr(skeleton, "confirm_proceed", lambda prompt: pytest.fail("unexpected prompt"))

    assert skeleton.main(["--ini", str(ini_path), "--no-console"]) == 0


def test_main_no_console_creates_file_logger_with_console_false(tmp_path, monkeypatch):
    ini_path = write_fake_ini(tmp_path)
    logger_calls, _logger = patch_logger(monkeypatch)
    patch_successful_db(monkeypatch)
    patch_successful_program_logic(monkeypatch)

    assert skeleton.main(["--ini", str(ini_path), "--no-console"]) == 0

    assert logger_calls == [
        {
            "name": "legacy_program_skeleton",
            "log_dir": tmp_path / "logs",
            "console": False,
        }
    ]


def test_main_manual_mode_uses_console_true(tmp_path, monkeypatch):
    ini_path = write_fake_ini(tmp_path)
    logger_calls, _logger = patch_logger(monkeypatch)
    patch_successful_db(monkeypatch)
    patch_successful_program_logic(monkeypatch)
    monkeypatch.setattr(skeleton, "can_prompt_user", lambda: False)

    assert skeleton.main(["--ini", str(ini_path)]) == 0

    assert logger_calls[0]["console"] is True


def test_main_manual_mode_prints_banner(tmp_path, monkeypatch):
    ini_path = write_fake_ini(tmp_path)
    patch_logger(monkeypatch)
    patch_successful_db(monkeypatch)
    patch_successful_program_logic(monkeypatch)
    monkeypatch.setattr(skeleton, "can_prompt_user", lambda: False)
    banner_calls = []
    monkeypatch.setattr(skeleton, "print_banner", lambda *args, **kwargs: banner_calls.append(args))

    assert skeleton.main(["--ini", str(ini_path)]) == 0

    assert len(banner_calls) == 1


def test_main_manual_mode_confirms_only_when_promptable(tmp_path, monkeypatch):
    ini_path = write_fake_ini(tmp_path)
    patch_logger(monkeypatch)
    patch_successful_db(monkeypatch)
    patch_successful_program_logic(monkeypatch)
    monkeypatch.setattr(skeleton, "can_prompt_user", lambda: True)
    confirm_calls = []
    monkeypatch.setattr(
        skeleton,
        "confirm_proceed",
        lambda prompt: confirm_calls.append(prompt) or True,
    )

    assert skeleton.main(["--ini", str(ini_path)]) == 0

    assert confirm_calls == ["Continue?"]


def test_main_manual_mode_does_not_confirm_when_stdin_is_not_promptable(
    tmp_path, monkeypatch
):
    ini_path = write_fake_ini(tmp_path)
    patch_logger(monkeypatch)
    patch_successful_db(monkeypatch)
    patch_successful_program_logic(monkeypatch)
    monkeypatch.setattr(skeleton, "can_prompt_user", lambda: False)
    monkeypatch.setattr(skeleton, "confirm_proceed", lambda prompt: pytest.fail("unexpected prompt"))

    assert skeleton.main(["--ini", str(ini_path)]) == 0


def test_main_declined_confirmation_returns_zero_and_skips_db(tmp_path, monkeypatch):
    ini_path = write_fake_ini(tmp_path)
    _logger_calls, logger = patch_logger(monkeypatch)
    monkeypatch.setattr(skeleton, "can_prompt_user", lambda: True)
    monkeypatch.setattr(skeleton, "confirm_proceed", lambda prompt: False)
    monkeypatch.setattr(
        skeleton,
        "create_mysql_connection",
        lambda config: pytest.fail("unexpected database connection"),
    )

    result = skeleton.main(["--ini", str(ini_path)])

    assert result == 0
    assert logger.warning_messages == ["Program cancelled by user"]


def test_successful_run_creates_db_runs_logic_closes_connection_and_returns_zero(
    tmp_path, monkeypatch
):
    ini_path = write_fake_ini(tmp_path)
    patch_logger(monkeypatch)
    db_calls, connection = patch_successful_db(monkeypatch)
    logic_calls = patch_successful_program_logic(monkeypatch)
    monkeypatch.setattr(skeleton, "can_prompt_user", lambda: False)

    result = skeleton.main(["--ini", str(ini_path)])

    assert result == 0
    assert len(db_calls) == 1
    assert len(logic_calls) == 1
    assert logic_calls[0]["connection"] is connection
    assert connection.closed is True


def test_run_logic_failure_logs_failure_closes_connection_and_returns_one(
    tmp_path, monkeypatch
):
    ini_path = write_fake_ini(tmp_path)
    _logger_calls, logger = patch_logger(monkeypatch)
    _db_calls, connection = patch_successful_db(monkeypatch)
    monkeypatch.setattr(skeleton, "can_prompt_user", lambda: False)

    def failing_run_program_logic(config, connection, log):
        raise RuntimeError("boom")

    monkeypatch.setattr(skeleton, "run_program_logic", failing_run_program_logic)

    result = skeleton.main(["--ini", str(ini_path)])

    assert result == 1
    assert logger.exception_messages == ["Program failed"]
    assert connection.closed is True


def test_main_tests_do_not_call_real_mysql(tmp_path, monkeypatch):
    ini_path = write_fake_ini(tmp_path)
    patch_logger(monkeypatch)
    db_calls, _connection = patch_successful_db(monkeypatch)
    patch_successful_program_logic(monkeypatch)

    assert skeleton.main(["--ini", str(ini_path), "--no-console"]) == 0

    assert len(db_calls) == 1
