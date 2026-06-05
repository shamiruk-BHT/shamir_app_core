import pytest

from shamir_app_core.config.provider import LegacyIniConfigProvider
from shamir_app_core.context import LegacyApplicationContext
from shamir_app_core.errors import FatalError


def test_context_loads_explicit_fixture_and_environment():
    context = LegacyApplicationContext(
        ini_path="tests/fixtures/legacy_sample.ini",
        progname="MiXeDProgram",
        environ={"USERNAME": "alice", "COMPUTERNAME": "workstation"},
    )

    assert context.runtime.program_name == "MiXeDProgram"
    assert context.runtime.username == "alice"
    assert context.runtime.machine_name == "workstation"
    assert context.paths.config_file.as_posix() == "tests/fixtures/legacy_sample.ini"
    assert context.paths.logs_dir.as_posix() == "tests/fixtures/logs"
    assert isinstance(context.config_provider, LegacyIniConfigProvider)
    assert context.config is context.config_provider
    assert context.config.get("MiXeDProgram", "Name") == "mixed case section"
    assert context.program_section == "MiXeDProgram"


def test_context_does_not_expose_direct_runtime_identity_aliases():
    context = LegacyApplicationContext(
        ini_path="tests/fixtures/legacy_sample.ini",
        progname="MiXeDProgram",
        environ={"USERNAME": "alice", "COMPUTERNAME": "workstation"},
    )

    assert not hasattr(context, "program_name")
    assert not hasattr(context, "progname")
    assert not hasattr(context, "username")
    assert not hasattr(context, "machine_name")
    assert not hasattr(context, "computername")


def test_context_missing_username_raises_key_error():
    with pytest.raises(KeyError):
        LegacyApplicationContext(
            ini_path="tests/fixtures/legacy_sample.ini",
            progname="MiXeDProgram",
            environ={"COMPUTERNAME": "workstation"},
        )


def test_context_missing_computername_raises_key_error():
    with pytest.raises(KeyError):
        LegacyApplicationContext(
            ini_path="tests/fixtures/legacy_sample.ini",
            progname="MiXeDProgram",
            environ={"USERNAME": "alice"},
        )


def test_context_missing_ini_raises_fatal_error(tmp_path):
    missing_path = tmp_path / "missing.ini"

    with pytest.raises(FatalError):
        LegacyApplicationContext(
            ini_path=missing_path,
            progname="MiXeDProgram",
            environ={"USERNAME": "alice", "COMPUTERNAME": "workstation"},
        )


def test_context_preserves_program_section_fallback():
    context = LegacyApplicationContext(
        ini_path="tests/fixtures/legacy_sample.ini",
        progname="MissingProgram",
        environ={"USERNAME": "alice", "COMPUTERNAME": "workstation"},
    )

    assert context.program_section == "MissingProgram"


def test_context_requires_explicit_ini_path():
    with pytest.raises(TypeError):
        LegacyApplicationContext(
            progname="MiXeDProgram",
            environ={"USERNAME": "alice", "COMPUTERNAME": "workstation"},
        )
