"""Reference startup skeleton for future migrated Shamir programs.

This file demonstrates the expected runtime shape for migrated console programs.
It is not a production job and contains no business processing.
"""

import argparse

from shamir_app_core import (
    LegacyApplicationContext,
    can_prompt_user,
    confirm_proceed,
    create_logger,
    create_mysql_connection,
    print_banner,
)


PROGRAM_NAME = "legacy_program_skeleton"


def parse_args(argv=None):
    """Parse only the example runtime arguments: --ini and --no-console."""
    parser = argparse.ArgumentParser(
        description="Reference skeleton for a migrated Shamir program."
    )
    parser.add_argument(
        "--ini",
        required=True,
        help="Path to the legacy INI file used by this program.",
    )
    parser.add_argument(
        "--no-console",
        action="store_true",
        help="Disable console output and prompts for Task Scheduler or automation.",
    )
    return parser.parse_args(argv)


def run_program_logic(config, connection, log):
    """Run program-specific work after startup setup has completed.

    Real migrations should put business logic here or call imported processing
    modules from here, keeping startup, logging, prompts, and DB setup separate.
    """
    log.info("Program-specific logic would run here")
    return 0


def main(argv=None):
    """Run the migrated-program startup flow and return a process exit code.

    The flow parses arguments, creates context, configures logging, optionally
    shows a banner and proceed prompt, creates the DB connection, calls program
    logic, closes the DB connection, and returns an exit code.
    """
    args = parse_args(argv)
    console_enabled = not args.no_console
    connection = None
    log = None

    try:
        context = LegacyApplicationContext(
            ini_path=args.ini,
            progname=PROGRAM_NAME,
        )
        log = create_logger(
            name=context.runtime.program_name,
            log_dir=context.paths.logs_dir,
            console=console_enabled,
        )
        log.info("Program started")

        if console_enabled:
            print_banner(
                "Legacy Program Skeleton",
                "Reference startup pattern for future migrated Shamir programs.",
            )

        if console_enabled and can_prompt_user():
            if not confirm_proceed("Continue?"):
                log.warning("Program cancelled by user")
                return 0

        log.info("Creating MySQL connection")
        connection = create_mysql_connection(context.config)
        log.info("MySQL connection created")

        exit_code = run_program_logic(
            config=context.config,
            connection=connection,
            log=log,
        )
        log.info("Program completed successfully")
        return exit_code
    except Exception:
        if log is not None:
            log.exception("Program failed")
        return 1
    finally:
        if connection is not None:
            connection.close()
            if log is not None:
                log.info("MySQL connection closed")


if __name__ == "__main__":
    raise SystemExit(main())
