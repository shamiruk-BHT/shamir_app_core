from shamir_app_core.context import LegacyApplicationContext
from shamir_app_core.runtime.paths import LegacyRuntimePaths


def test_minimal_migrated_legacy_script_uses_explicit_runtime_context():
    paths = LegacyRuntimePaths(config_path="tests/fixtures/legacy_sample.ini")
    context = LegacyApplicationContext(
        ini_path=paths.config_path,
        progname="mixedprogram",
        environ={"USERNAME": "alice", "COMPUTERNAME": "workstation"},
    )

    name = context.config.require("Name")
    retries = context.config.requireint("Retries")
    enabled = context.config.requireboolean("Enabled")

    assert context.runtime.username == "alice"
    assert context.runtime.machine_name == "workstation"
    assert context.program_section == "MiXeDProgram"
    assert context.config is context.config_provider
    assert name == "mixed case section"
    assert retries == 7
    assert enabled is False
