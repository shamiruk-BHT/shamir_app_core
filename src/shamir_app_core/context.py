"""Small legacy application context composition."""

from shamir_app_core.config.provider import LegacyIniConfigProvider
from shamir_app_core.runtime.identity import RuntimeIdentity
from shamir_app_core.runtime.paths import LegacyRuntimePaths


class LegacyApplicationContext:
    """Compose explicit legacy runtime identity and INI configuration.

    Runtime identity is exposed through ``context.runtime``.
    """

    def __init__(self, ini_path, progname, environ=None):
        """Create a context from an explicit INI path, program name, and environment."""
        self.runtime = RuntimeIdentity(environ, program_name=progname)
        # Preserve legacy fail-fast behavior for required runtime identity.
        self.runtime.getusername()
        self.runtime.gethostname()

        self.paths = LegacyRuntimePaths(config_path=ini_path)
        self.config_provider = LegacyIniConfigProvider(self.paths.config_file, progname)
        self.config = self.config_provider
        self.program_section = self.config_provider.program_section
