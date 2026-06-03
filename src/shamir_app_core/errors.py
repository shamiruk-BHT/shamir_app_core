"""Legacy-compatible application exception classes."""


class ApplicationInitError(Exception):
    """Exception indicating that application initialization cannot continue."""

    def __init__(self, message):
        self.value = message
        return None

    def __str__(self):
        return self.value


class FatalError(Exception):
    """Exception indicating that a fatal application error has occurred."""

    def __init__(self, message):
        self.value = message
        return None

    def __str__(self):
        return self.value


class RuntimeError(Exception):
    """Exception indicating that a non-fatal run-time error has occurred."""

    def __init__(self, message):
        self.value = message
        return None

    def __str__(self):
        return self.value
