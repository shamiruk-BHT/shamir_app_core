import pytest

from shamir_app_core.runtime.identity import RuntimeIdentity


def test_runtime_identity_reads_username():
    identity = RuntimeIdentity({"USERNAME": "alice", "COMPUTERNAME": "workstation"})

    assert identity.getusername() == "alice"


def test_runtime_identity_reads_computername():
    identity = RuntimeIdentity({"USERNAME": "alice", "COMPUTERNAME": "workstation"})

    assert identity.gethostname() == "workstation"


def test_runtime_identity_missing_username_raises_key_error():
    identity = RuntimeIdentity({"COMPUTERNAME": "workstation"})

    with pytest.raises(KeyError):
        identity.getusername()


def test_runtime_identity_missing_computername_raises_key_error():
    identity = RuntimeIdentity({"USERNAME": "alice"})

    with pytest.raises(KeyError):
        identity.gethostname()
