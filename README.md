# shamir_app_core

`shamir_app_core` is a small shared Python infrastructure package for migrating
selected Shamir legacy helpers into explicit, testable components.

It is a modern successor to selected pieces of legacy `application.py` and
`mmm.py`, supporting gradual refactoring of existing legacy Python scripts and
future C# to Python migrations. It is not a full clone of the legacy
`Application` object.

## Purpose

Use this package when a migrated script needs a narrow compatibility helper for:

- legacy-compatible fatal errors
- explicit legacy INI configuration loading
- required config value access
- runtime identity lookup from environment data
- explicit runtime path storage
- small explicit application logger setup
- minimal MySQL connection setup
- minimal composition of config and identity helpers
- legacy credential codec and `mmm.py` compatibility helpers

## Design Boundaries

The package intentionally keeps startup behavior visible to the caller:

- inputs are passed explicitly
- no production config auto-discovery
- no import-time work
- no global `Application` singleton
- no hidden global state
- no email or broad filesystem service setup
- no broad database service setup, query layer, repositories, ORM abstraction,
  or business-specific database logic
- no hidden logging auto-discovery or global logging configuration

If a script needs a config file, the caller provides the path. If a script needs
service setup, keep that setup outside this package until a focused helper is
defined and tested.

## Current Components

- `FatalError` and related legacy-compatible exception classes
- `LegacyIniConfigProvider`
  - `get()`
  - `getint()`
  - `getboolean()`
  - `has_option()`
  - `require("Option")` reads from the current program section
  - `require("host", section="mysql")` reads from an explicit named section
  - `requireint()` and `requireboolean()` support the same `section=` pattern
- `RuntimeIdentity`
  - `program_name`
  - `username`
  - `machine_name`
  - `getusername()`
  - `gethostname()`
- `LegacyRuntimePaths`
  - explicit `config_path`
  - `config_file` alias
  - optional `base_dir`
  - optional `logs_dir`
- `create_logger(name, log_dir, level=logging.INFO)`
  - writes `<log_dir>/<name>.log`
  - daily midnight rollover with `.YYYY-MM-DD` suffix
- `create_mysql_connection(config, section="mysql", decode_credentials=True)`
  - reads MySQL connection settings from a named config section
  - decodes legacy encoded `user` and `password` values by default
  - returns the object from `mysql.connector.connect(...)`
- `LegacyApplicationContext`
  - `LegacyApplicationContext(ini_path, progname, environ=None)`
  - runtime identity access through `context.runtime.program_name`,
    `context.runtime.username`, `context.runtime.machine_name`
  - `context.paths.logs_dir`
  - `context.config` aliases `context.config_provider`
  - raw parser remains available through `context.config_provider.parser`
- `shamir_app_core.compat.mmm`
- `shamir_app_core.credentials.codec`

## Development

Install or update the project environment:

```powershell
uv sync
```

Run the full test suite:

```powershell
uv run pytest
```

## Preferred Imports

```python
from shamir_app_core import (
    FatalError,
    LegacyApplicationContext,
    create_logger,
    create_mysql_connection,
)
from shamir_app_core.config import LegacyIniConfigProvider
from shamir_app_core.runtime import LegacyRuntimePaths, RuntimeIdentity
from shamir_app_core.compat import mmm
from shamir_app_core.credentials.codec import LegacyCredentialsCodec
```

## Minimal Usage

```python
from shamir_app_core.context import LegacyApplicationContext
from shamir_app_core.runtime import LegacyRuntimePaths
from shamir_app_core import create_logger, create_mysql_connection

paths = LegacyRuntimePaths(
    config_path="C:/path/to/shamiruk.ini",
)

context = LegacyApplicationContext(
    ini_path=paths.config_path,
    progname="MiXeDProgram",
    environ={
        "USERNAME": "alice",
        "COMPUTERNAME": "workstation",
    },
)

name = context.config.require("Name")
retries = context.config.requireint("Retries")
enabled = context.config.requireboolean("Enabled")

log = create_logger(
    name=context.runtime.program_name,
    log_dir=context.paths.logs_dir,
)
log.info("Program started")

connection = create_mysql_connection(context.config)
connection.close()

print(context.runtime.username, context.runtime.machine_name, name, retries, enabled)
```

In production code, pass the actual configuration path and normally omit
`environ` so `RuntimeIdentity` reads `os.environ`. In tests, pass a small
environment mapping to make runtime identity deterministic.

## Migration Notes

See [docs/migrating-legacy-scripts.md](docs/migrating-legacy-scripts.md) for
more detailed migration guidance and component responsibilities.
