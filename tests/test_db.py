import importlib

import pytest

from shamir_app_core.compat import mmm
from shamir_app_core.db import create_mysql_connection
from shamir_app_core.errors import FatalError


class FakeConfig:
    def __init__(self, values):
        self.values = values
        self.required_calls = []
        self.required_int_calls = []

    def require(self, option, *, section=None):
        self.required_calls.append((option, section))
        key = (section, option)
        if key not in self.values:
            raise FatalError(
                f"Required config option {option} in section {section} does not exist"
            )
        return self.values[key]

    def requireint(self, option, *, section=None):
        self.required_int_calls.append((option, section))
        return int(self.require(option, section=section))

    def has_option(self, section, option):
        return (section, option) in self.values


def mysql_values(section="mysql", overrides=None):
    values = {
        (section, "host"): "db.example.test",
        (section, "user"): mmm.encode("dbuser"),
        (section, "password"): mmm.encode("dbpass"),
        (section, "database"): "daily_figures",
    }
    if overrides is not None:
        values.update(overrides)
    return values


def test_create_mysql_connection_reads_values_from_mysql_section(monkeypatch):
    config = FakeConfig(mysql_values())
    monkeypatch.setattr(
        "shamir_app_core.db.mysql.connector.connect",
        lambda **kwargs: object(),
    )

    create_mysql_connection(config)

    assert ("host", "mysql") in config.required_calls
    assert ("user", "mysql") in config.required_calls
    assert ("password", "mysql") in config.required_calls
    assert ("database", "mysql") in config.required_calls


def test_create_mysql_connection_calls_connector_with_decoded_values(monkeypatch):
    captured = {}
    connection = object()
    config = FakeConfig(mysql_values())

    def connect(**kwargs):
        captured.update(kwargs)
        return connection

    monkeypatch.setattr("shamir_app_core.db.mysql.connector.connect", connect)

    result = create_mysql_connection(config)

    assert result is connection
    assert captured == {
        "host": "db.example.test",
        "user": "dbuser",
        "password": "dbpass",
        "database": "daily_figures",
        "port": 3306,
    }


def test_decode_credentials_false_passes_credentials_unchanged(monkeypatch):
    captured = {}
    config = FakeConfig(mysql_values())

    def connect(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("shamir_app_core.db.mysql.connector.connect", connect)

    create_mysql_connection(config, decode_credentials=False)

    assert captured["user"] == mmm.encode("dbuser")
    assert captured["password"] == mmm.encode("dbpass")


def test_missing_required_config_value_raises_fatal_error(monkeypatch):
    values = mysql_values()
    del values[("mysql", "password")]
    config = FakeConfig(values)
    monkeypatch.setattr(
        "shamir_app_core.db.mysql.connector.connect",
        lambda **kwargs: object(),
    )

    with pytest.raises(FatalError):
        create_mysql_connection(config)


def test_port_defaults_to_3306_when_missing(monkeypatch):
    captured = {}
    config = FakeConfig(mysql_values())

    def connect(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("shamir_app_core.db.mysql.connector.connect", connect)

    create_mysql_connection(config)

    assert captured["port"] == 3306


def test_port_from_config_is_passed_as_int(monkeypatch):
    captured = {}
    config = FakeConfig(mysql_values(overrides={("mysql", "port"): "3307"}))

    def connect(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("shamir_app_core.db.mysql.connector.connect", connect)

    create_mysql_connection(config)

    assert captured["port"] == 3307
    assert config.required_int_calls == [("port", "mysql")]


def test_create_mysql_connection_does_not_require_legacy_application_context(
    monkeypatch,
):
    config = FakeConfig(
        mysql_values("shared_mysql", overrides={("shared_mysql", "port"): "3308"})
    )
    captured = {}

    def connect(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("shamir_app_core.db.mysql.connector.connect", connect)

    create_mysql_connection(config, section="shared_mysql")

    assert captured["host"] == "db.example.test"
    assert captured["port"] == 3308


def test_importing_db_module_does_not_attempt_connection(monkeypatch):
    def fail_connect(**kwargs):
        raise AssertionError("connect should not be called during import")

    monkeypatch.setattr("shamir_app_core.db.mysql.connector.connect", fail_connect)

    importlib.reload(importlib.import_module("shamir_app_core.db"))
