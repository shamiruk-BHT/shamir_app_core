"""Legacy-compatible INI configuration provider."""

import configparser
from pathlib import Path

from shamir_app_core.errors import FatalError


class LegacyIniConfigProvider:
    """Load an explicit legacy INI file and expose ConfigParser-compatible access."""

    def __init__(self, path, progname):
        """Load path and resolve progname case-insensitively, raising FatalError if missing."""
        self.path = Path(path)
        self.progname = progname
        self.parser = configparser.ConfigParser()

        if not self.path.is_file():
            raise FatalError(f"Configuration file {str(self.path).upper()} does not exist")

        loaded_paths = self.parser.read(self.path)
        if not loaded_paths:
            raise FatalError(f"Configuration file {str(self.path).upper()} does not exist")

        self.program_section = self.resolve_program_section(progname)

    def resolve_program_section(self, progname=None):
        """Return the matching section with original casing, or progname when none exists."""
        section_name = self.progname if progname is None else progname
        for section in self.parser.sections():
            if section.lower() == section_name.lower():
                return section
        return section_name

    def get(self, section, option, *args, **kwargs):
        """Delegate to ConfigParser.get() with legacy parser behavior preserved."""
        return self.parser.get(section, option, *args, **kwargs)

    def getint(self, section, option, *args, **kwargs):
        """Delegate to ConfigParser.getint() with legacy parser behavior preserved."""
        return self.parser.getint(section, option, *args, **kwargs)

    def getboolean(self, section, option, *args, **kwargs):
        """Delegate to ConfigParser.getboolean() with legacy parser behavior preserved."""
        return self.parser.getboolean(section, option, *args, **kwargs)

    def require(self, option, *, section=None):
        """Return a required string option, raising FatalError when it is missing."""
        required_section = self._require_section_and_option(option, section)
        return self.get(required_section, option)

    def requireint(self, option, *, section=None):
        """Return a required integer option, raising FatalError when it is missing."""
        required_section = self._require_section_and_option(option, section)
        return self.getint(required_section, option)

    def requireboolean(self, option, *, section=None):
        """Return a required boolean option, raising FatalError when it is missing."""
        required_section = self._require_section_and_option(option, section)
        return self.getboolean(required_section, option)

    def has_option(self, section, option):
        """Delegate to ConfigParser.has_option() with legacy parser behavior preserved."""
        return self.parser.has_option(section, option)

    def sections(self):
        """Delegate to ConfigParser.sections() with legacy parser behavior preserved."""
        return self.parser.sections()

    def _require_section_and_option(self, option, section=None):
        required_section = self.program_section if section is None else section
        if not self.parser.has_section(required_section):
            raise FatalError(f"Required config section {required_section} does not exist")
        if not self.parser.has_option(required_section, option):
            raise FatalError(
                f"Required config option {option} in section {required_section} does not exist"
            )
        return required_section
