import logging
import math
import os
from typing import Optional

from exceptions.ftx_algotrading_exception import FtxAlgotradingException


def expand_var_and_user(path) -> str:
    return os.path.expanduser(os.path.expandvars(path))


def check_fields_in_dict(dictionary, fields, dictionary_name) -> bool:
    """
    Check that the fields are in the dict and raise an exception if not

    :param dictionary: The dictionary in which the check has to be done
    :type dictionary: dict
    :param fields: List of fields to check
    :type fields: list[str]
    :param dictionary_name: name of the dictionary (for exception message purpose)
    :type dictionary_name: str
    :return: True if all the fields are in the given dictionary, raise an exception otherwise
    """
    for field in fields:
        if field not in dictionary:
            raise FtxAlgotradingException("%s field(s) required but not found in %s: %s"
                                          % (", ".join(fields), dictionary_name, str(dictionary)))
    return True


def format_raw_data(raw_data: dict, time_step: int) -> Optional[dict]:
    """
    Format raw data

    :param raw_data: The raw data
    :param time_step: The time between each record
    :return: The formatted data list
    """
    if all(required_field in raw_data for required_field in ["time", "open", "high", "low", "close", "volume"]):
        return {
            "id": int(math.floor(raw_data["time"] / 1000) / time_step),
            "time": math.floor(raw_data["time"] / 1000),
            "open": float(raw_data["open"]),
            "high": float(raw_data["high"]),
            "low": float(raw_data["low"]),
            "close": float(raw_data["close"]),
            "volume": float(raw_data["volume"]),
        }
    else:
        logging.warning(
            "Data should be composed of 6 fields: <startTime>, <open>, <high>, <low>, <close>, <volume>")

    return None
