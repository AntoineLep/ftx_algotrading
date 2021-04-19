import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from tools.utils import expand_var_and_user


def init_logger(log_level: str, log_location: str, app_name: str) -> None:
    """
    Setup logger

    :param log_level: The log level to apply
    :param log_location: The path where to store the log files
    :param app_name:  The application name
    """
    # Getting log level
    log_level = _define_log_level(log_level)

    # Modify logger log level
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Set file formatter
    formatter = logging.Formatter("%(asctime)s :: %(levelname)s :: " + app_name + " ::  %(message)s")

    log_filename = "%s_log.txt" % app_name
    log_location = expand_var_and_user(log_location)

    Path(log_location).mkdir(parents=True, exist_ok=True)
    log_file_path = os.path.join(log_location, log_filename)
    need_roll = os.path.isfile(log_file_path)

    # Redirect logs into a log file
    file_handler = RotatingFileHandler(log_file_path, backupCount=10, maxBytes=2 * 1024 * 1024)
    file_handler.setLevel(log_level)
    if need_roll:
        file_handler.doRollover()
    logger.addHandler(file_handler)

    # Set formatter for each handler
    [handler.setFormatter(formatter) for handler in logger.handlers]


def _define_log_level(log_level: str) -> int:
    """
    Define the log level

    :param log_level: The log level to be defined: debug, info, warning, error, critical
    :return: Log level
    """
    if isinstance(log_level, str):
        if log_level.upper() == "DEBUG":
            return logging.DEBUG
        if log_level.upper() == "INFO":
            return logging.INFO
        if log_level.upper() == "WARNING":
            return logging.WARNING
        if log_level.upper() == "ERROR":
            return logging.ERROR
        if log_level.upper() == "CRITICAL":
            return logging.CRITICAL
    return logging.DEBUG
