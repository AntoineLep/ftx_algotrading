import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from tools.utils import expand_var_and_user


def init_logger(log_level, log_location, app_name) -> None:
    """
    Setup logger

    :param log_level: The log level to apply
    :type log_level: str
    :param log_location: The path where to store the log files
    :type log_location: str
    :param app_name:  The application name
    :type app_name: str
    :return: None
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
    file_handler.setFormatter(formatter)
    if need_roll:
        file_handler.doRollover()
    logger.addHandler(file_handler)

    # Redirect logs into the user console
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


def _define_log_level(log_level) -> str:
    """
    Define the log level

    :param log_level: The log level to be defined: debug, info, warning, error, critical
    :type log_level: str
    :return: None
    """
    if isinstance(log_level, str):
        if log_level.upper() == "debug":
            return logging.DEBUG
        if log_level.upper() == "info":
            return logging.INFO
        if log_level.upper() == "warning":
            return logging.WARNING
        if log_level.upper() == "error":
            return logging.ERROR
        if log_level.upper() == "critical":
            return logging.CRITICAL
    return logging.DEBUG
