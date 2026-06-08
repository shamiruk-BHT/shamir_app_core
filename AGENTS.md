# AGENTS.md — shamir_app_core

## Project overview

`shamir_app_core` is a small shared Python infrastructure package for Shamir legacy/migration programs.

It provides explicit, testable runtime foundations for migrated legacy Python scripts and future rewritten internal tools.

The package is a modern successor to selected pieces of legacy `application.py` and `mmm.py`, but it is not a full clone of the old `Application` object.

## Main goals

When working in this repository, prioritize:

1. Small, explicit runtime helpers.
2. Legacy compatibility where it is genuinely needed.
3. Testable behavior.
4. Clear public API with one preferred way to do each thing.
5. Offline/server-friendly deployment assumptions.
6. Simple code that a solo maintainer can understand.

## Core responsibilities

`shamir_app_core` may contain infrastructure such as:

* Legacy INI config loading.
* Required config access.
* Runtime identity.
* Runtime paths.
* Application/file logging.
* Console/banner/proceed helpers.
* Minimal MySQL connection helper.
* Legacy `mmm.py` / credential codec compatibility.
* Legacy-compatible errors.

`shamir_app_core` must not contain business/job logic such as:

* `filterEDI` processing.
* `makeEdiorder` processing.
* `makeIConduct` processing.
* Customer/report business rules.
* EDI transformation logic.
* Query/report implementations.
* Dataset transformation engines.
* Task-specific exports.

Program-specific logic belongs in a separate future project such as `shamir_jobs`.

## Architectural boundaries

Keep the package boring and explicit.

Do not add:

* A global `Application` singleton.
* A service container.
* A plugin framework.
* A query builder.
* Repository abstractions.
* ORM abstractions.
* Django integration.
* Runtime config auto-discovery.
* Hidden logging auto-discovery.
* Hidden database connection state.
* Background downloads.
* GitHub/runtime install assumptions.

Prefer explicit calls such as:

```python
context.runtime.program_name
context.config.require("Option")
context.config.require("host", section="mysql")
create_logger(name, log_dir, console=...)
create_mysql_connection(config)
```

Avoid adding multiple aliases for the same information.

If there are two or three ways to access the same value, simplify toward one canonical API.

## Current canonical API direction

Runtime identity:

```python
context.runtime.program_name
context.runtime.username
context.runtime.machine_name
```

Config values from the current program section:

```python
config.require("Option")
config.requireint("Retries")
config.requireboolean("Enabled")
```

Config values from shared/named sections:

```python
config.require("host", section="mysql")
config.requireint("port", section="mysql")
config.requireboolean("enabled", section="some_section")
```

Logger:

```python
log = create_logger(
    name=context.runtime.program_name,
    log_dir=context.paths.logs_dir,
    console=console_enabled,
)
```

DB helper:

```python
connection = create_mysql_connection(context.config)
```

Console/manual mode helpers:

```python
print_banner(...)
confirm_proceed(...)
can_prompt_user()
```

## Offline deployment constraint

Production servers may have no internet access.

Do not design runtime behavior that depends on:

* Internet access.
* GitHub access.
* Runtime package downloads.
* Dev-machine paths such as `D:\Shamir\dev\...`.
* `file:///D:/Shamir/dev/...` dependencies in production.

Future deployment should use offline/self-contained release bundles:

* Build wheels on a dev machine.
* Build a local wheelhouse.
* Copy the release bundle to the server.
* Install from local files only.
* Run through Task Scheduler wrappers.

## Safety rules

Do not expose, print, copy, commit, or summarize real secrets or credentials.

Be especially careful with:

* Real `shamiruk.ini`.
* Database credentials.
* Encoded/decoded passwords.
* Internal hostnames.
* Private connection strings.
* Logs.
* Generated output files.
* Real customer/business data.
* Production file paths.

When inspecting real legacy files such as `application.py`, `mmm.py`, or dev `shamiruk.ini`, treat them as read-only references unless explicitly asked otherwise.

Never copy real secret values into tests, docs, examples, or reports.

## Default working mode

Default to small, reviewable changes.

Before editing:

1. Inspect the existing implementation.
2. Explain whether the functionality already exists.
3. Prefer improving names/docs/tests over adding new APIs.
4. Avoid aliases unless there is a strong compatibility reason.
5. Preserve existing behavior unless the user explicitly approves behavior changes.

Do not commit or push unless explicitly asked.

## Testing and verification

Use `uv`.

Run the full test suite with:

```powershell
uv run pytest
```

Tests should:

* Avoid real MySQL connections.
* Mock external effects.
* Use `tmp_path` for files.
* Avoid real `shamiruk.ini`.
* Avoid real secrets.
* Avoid committing logs or generated files.
* Cover failure paths where practical.

The project uses a repo-local pytest temp directory. Do not remove that setup without a specific reason.

## Code style

Prefer:

* Small functions.
* Explicit names.
* Type hints where helpful.
* Clear docstrings for public helpers and examples.
* Normal Python standard library behavior where possible.
* Simple wrappers around standard tools rather than custom frameworks.

Avoid:

* Large abstractions.
* Hidden global state.
* Silent exception swallowing.
* Broad utility modules with unclear scope.
* Magic behavior based on environment guessing.
* Repeated ways to do the same thing.

## Documentation style

Keep README and docs practical.

Document:

* What the helper does.
* How to use it.
* What it deliberately does not do.
* Which access path is canonical.

Avoid long theoretical explanations.

## Reporting format after changes

After implementation, report:

1. Files changed.
2. Exact test command and result.
3. Public API added or changed.
4. Important behavior changes.
5. How the change stays within project boundaries.
6. Anything awkward or potentially over-engineered.
7. `git status --short -uall`.

Do not claim success if tests were not run.
