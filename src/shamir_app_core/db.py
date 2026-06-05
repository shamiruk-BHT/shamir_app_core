"""Minimal database connection helpers."""

import mysql.connector

from shamir_app_core.compat import mmm


def create_mysql_connection(config, *, section="mysql", decode_credentials=True):
    """Create a MySQL connection from a config-provider-like object."""
    user = config.require("user", section=section)
    password = config.require("password", section=section)

    if decode_credentials:
        user = mmm.decode(user)
        password = mmm.decode(password)

    connection_args = {
        "host": config.require("host", section=section),
        "user": user,
        "password": password,
        "database": config.require("database", section=section),
        "port": (
            config.requireint("port", section=section)
            if config.has_option(section, "port")
            else 3306
        ),
    }

    return mysql.connector.connect(**connection_args)
