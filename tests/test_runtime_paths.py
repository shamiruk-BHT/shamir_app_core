from pathlib import Path

from shamir_app_core.runtime.paths import LegacyRuntimePaths


def test_runtime_paths_stores_config_path_as_path():
    paths = LegacyRuntimePaths(config_path="config/shamiruk.ini")

    assert paths.config_path == Path("config/shamiruk.ini")


def test_runtime_paths_defaults_base_dir_to_config_parent():
    paths = LegacyRuntimePaths(config_path="config/shamiruk.ini")

    assert paths.base_dir == Path("config")


def test_runtime_paths_uses_explicit_base_dir_when_provided():
    paths = LegacyRuntimePaths(
        config_path="config/shamiruk.ini",
        base_dir="runtime",
    )

    assert paths.base_dir == Path("runtime")


def test_runtime_paths_accepts_path_objects():
    config_path = Path("config") / "shamiruk.ini"
    base_dir = Path("runtime")

    paths = LegacyRuntimePaths(config_path=config_path, base_dir=base_dir)

    assert paths.config_path == config_path
    assert paths.base_dir == base_dir


def test_runtime_paths_does_not_require_config_file_to_exist():
    paths = LegacyRuntimePaths(config_path="missing/shamiruk.ini")

    assert paths.config_path == Path("missing/shamiruk.ini")
