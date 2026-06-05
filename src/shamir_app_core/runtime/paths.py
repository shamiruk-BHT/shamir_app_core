"""Side-effect-free runtime path helpers for legacy compatibility."""

from pathlib import Path


class LegacyRuntimePaths:
    """Store explicit runtime paths without discovery or filesystem access."""

    def __init__(self, *, config_path=None, config_file=None, base_dir=None, logs_dir=None):
        """Create runtime paths from explicit path values."""
        if config_path is None and config_file is None:
            raise TypeError("config_path or config_file is required")

        self.config_file = Path(config_path if config_file is None else config_file)
        self.config_path = self.config_file
        self.base_dir = self.config_file.parent if base_dir is None else Path(base_dir)
        self.logs_dir = self.base_dir / "logs" if logs_dir is None else Path(logs_dir)
