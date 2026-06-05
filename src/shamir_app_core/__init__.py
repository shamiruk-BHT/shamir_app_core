"""Core compatibility helpers for legacy Shamir Python applications."""

from shamir_app_core.app_logging import create_logger
from shamir_app_core.context import LegacyApplicationContext
from shamir_app_core.errors import ApplicationInitError, FatalError, RuntimeError

__all__ = [
    "ApplicationInitError",
    "create_logger",
    "FatalError",
    "LegacyApplicationContext",
    "RuntimeError",
]
