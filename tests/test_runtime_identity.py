import pytest

from shamir_app_core.runtime.identity import RuntimeIdentity


def test_runtime_identity_reads_username():
    identity = RuntimeIdentity({"USERNAME": "alice", "COMPUTERNAME": "workstation"})

    assert identity.getusername() == "alice"


def test_runtime_identity_reads_computername():
    identity = RuntimeIdentity({"USERNAME": "alice", "COMPUTERNAME": "workstation"})

    assert identity.gethostname() == "workstation"


def test_runtime_identity_exposes_program_name_from_argv():
    identity = RuntimeIdentity(
        {"USERNAME": "alice", "COMPUTERNAME": "workstation"},
        argv=["C:/jobs/daily_figures.py"],
    )

    assert identity.program_name == "daily_figures"


def test_runtime_identity_program_name_allows_explicit_override():
    identity = RuntimeIdentity(
        {"USERNAME": "alice", "COMPUTERNAME": "workstation"},
        program_name="explicit_job",
        argv=["C:/jobs/daily_figures.py"],
    )

    assert identity.program_name == "explicit_job"


def test_runtime_identity_exposes_runtime_properties():
    identity = RuntimeIdentity({"USERNAME": "alice", "COMPUTERNAME": "workstation"})

    assert identity.username == "alice"
    assert identity.machine_name == "workstation"


def test_runtime_identity_missing_username_raises_key_error():
    identity = RuntimeIdentity({"COMPUTERNAME": "workstation"})

    with pytest.raises(KeyError):
        identity.getusername()


def test_runtime_identity_missing_computername_raises_key_error():
    identity = RuntimeIdentity({"USERNAME": "alice"})

    with pytest.raises(KeyError):
        identity.gethostname()
