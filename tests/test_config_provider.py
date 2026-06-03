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
