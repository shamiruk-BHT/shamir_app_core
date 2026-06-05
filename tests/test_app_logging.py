import logging
import re
from logging.handlers import TimedRotatingFileHandler

from shamir_app_core import create_logger


def _close_logger(logger):
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def test_create_logger_creates_log_dir(tmp_path):
    log_dir = tmp_path / "missing-logs"
    logger = create_logger("creates_dir", log_dir)

    try:
        assert log_dir.is_dir()
    finally:
        _close_logger(logger)


def test_create_logger_writes_message_to_log_file(tmp_path):
    logger = create_logger("writes_message", tmp_path)

    try:
        logger.info("Program started")
        logger.handlers[0].flush()

        assert (tmp_path / "writes_message.log").read_text(
            encoding="utf-8"
        ).endswith(" | INFO    | Program started\n")
    finally:
        _close_logger(logger)


def test_create_logger_formats_timestamp_level_and_message(tmp_path):
    logger = create_logger("formats_message", tmp_path)

    try:
        logger.warning("No rows found")
        logger.handlers[0].flush()

        content = (tmp_path / "formats_message.log").read_text(encoding="utf-8")
        assert re.fullmatch(
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} "
            r"\| WARNING \| No rows found\n",
            content,
        )
    finally:
        _close_logger(logger)


def test_trace_level_works(tmp_path):
    logger = create_logger("trace_level", tmp_path, level="TRACE")

    try:
        logger.trace("Trace details")
        logger.handlers[0].flush()

        assert " | TRACE   | Trace details\n" in (
            tmp_path / "trace_level.log"
        ).read_text(encoding="utf-8")
    finally:
        _close_logger(logger)


def test_fatal_displays_as_fatal(tmp_path):
    logger = create_logger("fatal_level", tmp_path)

    try:
        logger.fatal("Program failed")
        logger.handlers[0].flush()

        assert " | FATAL   | Program failed\n" in (
            tmp_path / "fatal_level.log"
        ).read_text(encoding="utf-8")
    finally:
        _close_logger(logger)


def test_create_logger_twice_does_not_duplicate_messages(tmp_path):
    logger = create_logger("no_duplicates", tmp_path)
    same_logger = create_logger("no_duplicates", tmp_path)

    try:
        same_logger.info("Only once")
        same_logger.handlers[0].flush()

        content = (tmp_path / "no_duplicates.log").read_text(encoding="utf-8")
        assert content.count("Only once") == 1
        assert len(logger.handlers) == 1
    finally:
        _close_logger(logger)


def test_handler_uses_daily_midnight_rollover(tmp_path):
    logger = create_logger("rollover", tmp_path)

    try:
        handler = logger.handlers[0]

        assert isinstance(handler, TimedRotatingFileHandler)
        assert handler.when == "MIDNIGHT"
        assert handler.interval == 24 * 60 * 60
    finally:
        _close_logger(logger)


def test_rotated_suffix_uses_date_format(tmp_path):
    logger = create_logger("suffix", tmp_path)

    try:
        handler = logger.handlers[0]

        assert handler.suffix == "%Y-%m-%d"
    finally:
        _close_logger(logger)
