"""
btlogging sub-package standardized logging for Hetutensor.

This module provides logging functionality for the Hetutensor package. It includes custom loggers, handlers, and
formatters to ensure consistent logging throughout the project.
"""

from .loggingmachine import LoggingMachine


logging = LoggingMachine(LoggingMachine.config())
