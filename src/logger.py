import logging

class ColoredFormatter(logging.Formatter):
    """Add colors to log messages."""

    RED = "\033[91m"
    RESET = "\033[0m"

    def format(self, record):
        message = super().format(record)

        if record.levelno >= logging.WARNING:
            return f"{self.RED}{message}{self.RESET}"

        return message
