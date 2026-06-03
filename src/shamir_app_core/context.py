"""Small legacy application context composition."""

from shamir_app_core.config.provider import LegacyIniConfigProvider
from shamir_app_core.runtime.identity import RuntimeIdentity


class LegacyApplicationContext:
    """Compose explicit legacy runtime identity and INI configuration."""

    def __init__(self, ini_path, progname, environ=None):
        """Create a context from an explicit INI path, program name, and environment."""
        self.progname = progname

        identity = RuntimeIdentity(environ)
        self.username = identity.getusername()
        self.computername = identity.gethostname()

        self.config_provider = LegacyIniConfigProvider(ini_path, progname)
        self.config = self.config_provider
        self.program_section = self.config_provider.program_section
