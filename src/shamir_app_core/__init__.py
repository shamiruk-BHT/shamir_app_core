"""Core compatibility helpers for legacy Shamir Python applications."""

from shamir_app_core.app_logging import create_logger
from shamir_app_core.console import (
    can_prompt_user,
    confirm_proceed,
    format_banner,
    print_banner,
)
from shamir_app_core.context import LegacyApplicationContext
from shamir_app_core.db import create_mysql_connection
from shamir_app_core.event_log import JsonlEventWriter
from shamir_app_core.errors import ApplicationInitError, FatalError, RuntimeError

__all__ = [
    "ApplicationInitError",
    "can_prompt_user",
    "confirm_proceed",
    "create_logger",
    "create_mysql_connection",
    "FatalError",
    "format_banner",
    "JsonlEventWriter",
    "LegacyApplicationContext",
    "print_banner",
    "RuntimeError",
]
