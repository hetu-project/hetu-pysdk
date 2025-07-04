"""Btlogging constant definition module."""

BASE_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
TRACE_LOG_FORMAT = (
    f"%(asctime)s | %(levelname)s | %(name)s:%(filename)s:%(lineno)s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
HETUTENSOR_LOGGER_NAME = "hetutensor"
DEFAULT_LOG_FILE_NAME = "hetutensor.log"
DEFAULT_MAX_ROTATING_LOG_FILE_SIZE = 25 * 1024 * 1024
DEFAULT_LOG_BACKUP_COUNT = 10
