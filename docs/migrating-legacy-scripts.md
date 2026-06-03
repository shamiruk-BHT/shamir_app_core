# Migrating Legacy Scripts to `shamir_app_core`

`shamir_app_core` is a small compatibility package for migrating selected
legacy Shamir Python scripts away from the old `application.py` and `mmm.py`
style. It provides explicit, testable building blocks for the pieces scripts
still need: legacy INI loading, runtime identity lookup, runtime path storage,
and a minimal application context.

It is not a full clone of the legacy `Application` object. New migrations should
keep startup logic visible in the script that owns it.

## Design Principles

- Pass inputs explicitly.
- Do not auto-discover production configuration files.
- Do not perform work at import time.
- Do not create a global `Application` singleton.
- Prefer small composable objects over hidden global runtime state.
- Keep filesystem, database, email, and logging setup outside this package until
  a narrow migration need is defined.

## What This Package Does Not Do

`shamir_app_core` does not search for `shamiruk.ini`, read production
configuration by default, set up database connections, configure logging, send
email, or infer paths from the current working directory.

If a script needs a config file, the caller must provide the path. If a script
needs environment values, the caller either uses the real process environment or
passes a test mapping.

## Minimal Usage

```python
from shamir_app_core.context import LegacyApplicationContext
from shamir_app_core.runtime import LegacyRuntimePaths


paths = LegacyRuntimePaths(
    config_path="tests/fixtures/legacy_sample.ini",
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
dictionary to make identity lookup deterministic.

## Component Responsibilities

### `FatalError`

`FatalError` is the existing legacy-compatible fatal exception. Providers use it
when startup cannot continue, such as when a required INI file, section, or
option is missing.

### `LegacyIniConfigProvider`

`LegacyIniConfigProvider(path, progname)` loads one explicit INI file. It does
not search for files. It exposes:

- `parser`, the underlying `configparser.ConfigParser`
- `program_section`, resolved case-insensitively while preserving fixture casing
- `get()`, `getint()`, `getboolean()`, and `has_option()` for parser-compatible
  access
- `require()`, `requireint()`, and `requireboolean()` for required config values
  that raise `FatalError` on missing sections or options

When `section=` is omitted from a `require*` call, the provider reads from
`program_section`. Pass `section="Defaults"` or another explicit section when a
script needs shared settings.

### `RuntimeIdentity`

`RuntimeIdentity(environ=None)` reads legacy identity values from an environment
mapping. It provides:

- `getusername()` for `USERNAME`
- `gethostname()` for `COMPUTERNAME`

Missing values raise `KeyError`, matching the current legacy compatibility
behavior.

### `LegacyRuntimePaths`

`LegacyRuntimePaths(config_path=..., base_dir=None)` stores explicit runtime
paths as `pathlib.Path` objects. If `base_dir` is omitted, it defaults to
`config_path.parent`.

It does not check whether paths exist, read files, search directories, or infer
anything from the current process.

### `LegacyApplicationContext`

`LegacyApplicationContext(ini_path, progname, environ=None)` composes the
current config and identity helpers. It exposes:

- `progname`
- `username`
- `computername`
- `config_provider`
- `config`, an alias to `config_provider`
- `program_section`

Use it when a migrated script wants one small object containing the legacy
program identity and config provider. Do not add unrelated service setup to the
context.

## Migration Notes

Start each migration by identifying the script inputs: config path, program
name, and environment expectations. Pass those values explicitly near the script
entry point.

Prefer `require*` methods for configuration values that must exist before the
script can safely continue. Use parser-compatible `get*` methods only where the
legacy behavior intentionally allows parser defaults or optional handling.

Keep path selection outside `shamir_app_core`. A caller, test, scheduler, or
wrapper script should decide which config file to use before constructing these
objects.

Avoid recreating the legacy `Application` singleton. If a future migration needs
database, email, logging, or filesystem helpers, add them as separate explicit
components with focused tests rather than hiding them behind import-time startup
logic.
