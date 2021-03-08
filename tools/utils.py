import logging
import os

from exceptions.ftx_algotrading_exception import FtxAlgotradingException


def expand_var_and_user(path):
    return os.path.expanduser(os.path.expandvars(path))


def check_fields_in_dict(dictionary, fields, dictionary_name):
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


def format_raw_data(raw_data, time_step, result_key):
    """
    Format raw data

    :param raw_data: The raw data
    :type raw_data: dict
    :param time_step: The time between each record
    :type time_step: int
    :param result_key: Key to access data in raw_data dict
    :type result_key: str
    :return: The formatted data list
    :rtype: list
    """
    formatted_data = []
    check_fields_in_dict(raw_data, ["result"], "Raw data")
    check_fields_in_dict(raw_data["result"], [result_key], "Raw data")
    for data in raw_data["result"][result_key]:
        if len(data) == 8:
            formatted_data.append({
                "id": int(data[0] / time_step),
                "time": data[0],
                "open": float(data[1]),
                "high": float(data[2]),
                "low": float(data[3]),
                "close": float(data[4]),
                "vwap": float(data[5]),
                "volume": float(data[6]),
                "count": data[7]
            })
        else:
            logging.warning("Data should be composed of 8 fields: <time>, <open>, <high>, <low>, <close>, <vwap>, "
                            "<volume>, <count>")

    return formatted_data
