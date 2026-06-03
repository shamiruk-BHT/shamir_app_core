# shamir_app_core

Small compatibility-focused core package for migrating legacy Shamir Python
application helpers.

Milestone 1.1 includes only:

- legacy-compatible exception classes;
- the legacy credential codec used by `mmm.py`;
- a minimal `shamir_app_core.compat.mmm` facade;
- pytest coverage for the initial compatibility behavior.

This package does not implement the legacy `Application` adapter, database
access, configuration loading, filesystem purge helpers, or any production INI
file handling.

## Development

Install test dependencies, then run:

```powershell
python -m pytest
```
