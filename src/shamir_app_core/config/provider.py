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

    def has_option(self, section, option):
        """Delegate to ConfigParser.has_option() with legacy parser behavior preserved."""
        return self.parser.has_option(section, option)

    def sections(self):
        """Delegate to ConfigParser.sections() with legacy parser behavior preserved."""
        return self.parser.sections()
