"""Small application logging helpers."""

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


TRACE = 5


def _install_level_names():
    """Register project level names without replacing logging classes."""
    logging.addLevelName(TRACE, "TRACE")
    logging.TRACE = TRACE
    logging.addLevelName(logging.FATAL, "FATAL")

    if not hasattr(logging.Logger, "trace"):

        def trace(self, message, *args, **kwargs):
            if self.isEnabledFor(TRACE):
                self._log(TRACE, message, args, **kwargs)

        logging.Logger.trace = trace


class _AlignedLevelFormatter(logging.Formatter):
    def format(self, record):
        original_levelname = record.levelname
        record.levelname = original_levelname.ljust(7)
        try:
            return super().format(record)
        finally:
            record.levelname = original_levelname


def _normalize_level(level):
    if isinstance(level, str):
        level_name = level.upper()
        if level_name == "TRACE":
            return TRACE
        resolved_level = logging.getLevelName(level_name)
        if isinstance(resolved_level, int):
            return resolved_level
        raise ValueError(f"Unknown logging level: {level}")
    return level


def create_logger(name, log_dir, level=logging.INFO):
    """Create or return a standard logger writing daily rotating log files."""
    _install_level_names()

    log_path = Path(log_dir) / f"{name}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(_normalize_level(level))
    logger.propagate = False

    resolved_log_path = log_path.resolve()
    for handler in logger.handlers:
        if getattr(handler, "_shamir_app_core_log_path", None) == resolved_log_path:
            handler.setLevel(_normalize_level(level))
            return logger

    handler = TimedRotatingFileHandler(
        log_path,
        when="midnight",
        interval=1,
        backupCount=0,
        encoding="utf-8",
    )
    handler.suffix = "%Y-%m-%d"
    handler.setLevel(_normalize_level(level))
    handler.setFormatter(
        _AlignedLevelFormatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    handler._shamir_app_core_log_path = resolved_log_path

    logger.addHandler(handler)
    return logger
