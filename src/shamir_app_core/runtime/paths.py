"""Side-effect-free runtime path helpers for legacy compatibility."""

from pathlib import Path


class LegacyRuntimePaths:
    """Store explicit runtime paths without discovery or filesystem access."""

    def __init__(self, *, config_path, base_dir=None):
        """Create runtime paths from explicit path values."""
        self.config_path = Path(config_path)
        self.base_dir = self.config_path.parent if base_dir is None else Path(base_dir)
