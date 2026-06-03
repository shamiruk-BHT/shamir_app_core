"""Legacy-compatible runtime identity lookups."""

import os


class RuntimeIdentity:
    """Read legacy runtime identity values from an environment mapping."""

    def __init__(self, environ=None):
        """Create an identity reader using environ or os.environ."""
        self.environ = os.environ if environ is None else environ

    def getusername(self):
        """Return USERNAME, raising KeyError when legacy environment data is missing."""
        return self.environ["USERNAME"]

    def gethostname(self):
        """Return COMPUTERNAME, raising KeyError when legacy environment data is missing."""
        return self.environ["COMPUTERNAME"]
