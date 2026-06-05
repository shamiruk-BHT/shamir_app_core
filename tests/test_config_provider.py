import configparser

import pytest

from shamir_app_core.config.provider import LegacyIniConfigProvider
from shamir_app_core.errors import FatalError


def test_config_provider_loads_fixture_ini():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "MiXeDProgram")

    assert isinstance(provider.parser, configparser.ConfigParser)
    assert provider.sections() == ["Defaults", "MiXeDProgram"]


def test_config_provider_missing_ini_raises_fatal_error(tmp_path):
    missing_path = tmp_path / "missing.ini"

    with pytest.raises(FatalError):
        LegacyIniConfigProvider(missing_path, "Program")


def test_config_provider_section_resolution_preserves_original_casing():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    assert provider.resolve_program_section("mixedprogram") == "MiXeDProgram"
    assert provider.program_section == "MiXeDProgram"


def test_config_provider_section_resolution_falls_back_to_progname():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "MissingProgram")

    assert provider.resolve_program_section("MissingProgram") == "MissingProgram"
    assert provider.program_section == "MissingProgram"


def test_config_provider_raw_parser_supports_get():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    assert provider.parser.get("MiXeDProgram", "Name") == "mixed case section"
    assert provider.get("MiXeDProgram", "Name") == "mixed case section"


def test_config_provider_raw_parser_supports_getint():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    assert provider.parser.getint("MiXeDProgram", "Retries") == 7
    assert provider.getint("MiXeDProgram", "Retries") == 7


def test_config_provider_raw_parser_supports_getboolean():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    assert provider.parser.getboolean("MiXeDProgram", "Enabled") is False
    assert provider.getboolean("MiXeDProgram", "Enabled") is False


def test_config_provider_raw_parser_supports_has_option():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    assert provider.parser.has_option("MiXeDProgram", "Name") is True
    assert provider.has_option("MiXeDProgram", "Name") is True


def test_require_returns_value_from_program_section():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    assert provider.require("Name") == "mixed case section"


def test_require_returns_value_from_explicit_section():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    assert provider.require("Name", section="Defaults") == "fixture"


def test_requireint_returns_value_from_explicit_section():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    assert provider.requireint("Retries", section="Defaults") == 3


def test_requireboolean_returns_value_from_explicit_section():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    assert provider.requireboolean("Enabled", section="Defaults") is True


def test_require_raises_fatal_error_for_missing_option():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    with pytest.raises(FatalError):
        provider.require("MissingOption")


def test_require_raises_fatal_error_for_missing_section():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    with pytest.raises(FatalError):
        provider.require("Name", section="MissingSection")


def test_requireint_returns_integer():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    assert provider.requireint("Retries") == 7


def test_requireboolean_returns_boolean():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    assert provider.requireboolean("Enabled") is False


def test_require_error_message_includes_option_and_section():
    provider = LegacyIniConfigProvider("tests/fixtures/legacy_sample.ini", "mixedprogram")

    with pytest.raises(FatalError) as exc_info:
        provider.require("MissingOption", section="MiXeDProgram")

    message = str(exc_info.value)
    assert "MissingOption" in message
    assert "MiXeDProgram" in message
