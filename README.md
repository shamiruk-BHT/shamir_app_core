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
- minimal composition of config and identity helpers
- legacy credential codec and `mmm.py` compatibility helpers

## Design Boundaries

The package intentionally keeps startup behavior visible to the caller:

- inputs are passed explicitly
- no production config auto-discovery
- no import-time work
- no global `Application` singleton
- no hidden global state
- no database, logging, email, or filesystem service setup

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
  - `require()`
  - `requireint()`
  - `requireboolean()`
- `RuntimeIdentity`
  - `getusername()`
  - `gethostname()`
- `LegacyRuntimePaths`
  - explicit `config_path`
  - optional `base_dir`
- `LegacyApplicationContext`
  - `LegacyApplicationContext(ini_path, progname, environ=None)`
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
uv run python -m pytest
```

## Preferred Imports

```python
from shamir_app_core import FatalError, LegacyApplicationContext
from shamir_app_core.config import LegacyIniConfigProvider
from shamir_app_core.runtime import LegacyRuntimePaths, RuntimeIdentity
from shamir_app_core.compat import mmm
from shamir_app_core.credentials.codec import LegacyCredentialsCodec
```

## Minimal Usage

```python
from shamir_app_core.context import LegacyApplicationContext
from shamir_app_core.runtime import LegacyRuntimePaths


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

print(context.username, context.computername, name, retries, enabled)
```

In production code, pass the actual configuration path and normally omit
`environ` so `RuntimeIdentity` reads `os.environ`. In tests, pass a small
environment mapping to make runtime identity deterministic.

## Migration Notes

See [docs/migrating-legacy-scripts.md](docs/migrating-legacy-scripts.md) for
more detailed migration guidance and component responsibilities.
