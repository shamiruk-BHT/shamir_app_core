"""Legacy-compatible runtime identity lookups."""

import os
import sys
from pathlib import Path


class RuntimeIdentity:
    """Read legacy runtime identity values from an environment mapping."""

    def __init__(self, environ=None, program_name=None, argv=None):
        """Create an identity reader using environ or os.environ."""
        self.environ = os.environ if environ is None else environ
        self.program_name = (
            self._resolve_program_name(argv) if program_name is None else program_name
        )

    @property
    def username(self):
        """Return the current runtime username."""
        return self.getusername()

    @property
    def machine_name(self):
        """Return the current runtime machine name."""
        return self.gethostname()

    def getusername(self):
        """Return USERNAME, raising KeyError when legacy environment data is missing."""
        return self.environ["USERNAME"]

    def gethostname(self):
        """Return COMPUTERNAME, raising KeyError when legacy environment data is missing."""
        return self.environ["COMPUTERNAME"]

    def _resolve_program_name(self, argv):
        source_argv = sys.argv if argv is None else argv
        program_path = source_argv[0] if source_argv else ""
        return Path(program_path).stem or "python"
