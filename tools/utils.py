import logging
import math
import os
from typing import Optional

from core.models.market_data_dict import MarketDataDict
from core.models.raw_stock_data_dict import RawStockDataDict
from core.models.wallet_dict import WalletDict
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


def format_ohlcv_raw_data(ohlcv_raw_data: dict, time_step: int) -> Optional[RawStockDataDict]:
    """
    Format OHLCV raw data

    :param ohlcv_raw_data: The raw data
    :param time_step: The time between each record
    :return: The formatted data list
    """
    if all(required_field in ohlcv_raw_data for required_field in ["time", "open", "high", "low", "close", "volume"]):
        return {
            "id": int(math.floor(ohlcv_raw_data["time"] / 1000) / time_step),
            "time": math.floor(ohlcv_raw_data["time"] / 1000),
            "open_price": float(ohlcv_raw_data["open"]),
            "high_price": float(ohlcv_raw_data["high"]),
            "low_price": float(ohlcv_raw_data["low"]),
            "close_price": float(ohlcv_raw_data["close"]),
            "volume": float(ohlcv_raw_data["volume"]),
        }
    else:
        logging.warning(
            "Data should be composed of 6 fields: <time>, <open>, <high>, <low>, <close>, <volume>")

    return None


def format_market_raw_data(market_raw_data: dict) -> Optional[MarketDataDict]:
    """
    Format market raw data

    :param market_raw_data: The market raw data
    :return: The formatted data list
    """
    if all(required_field in market_raw_data for required_field in ["market", "price", "ask", "bid", "change1h",
                                                                    "change24h"]):
        return {
            "market": market_raw_data["market"],
            "price": float(market_raw_data["price"]),
            "ask": float(market_raw_data["ask"]),
            "bid": float(market_raw_data["bid"]),
            "change1h": float(market_raw_data["change1h"]),
            "change24h": float(market_raw_data["change24h"])
        }
    else:
        logging.warning(
            "Data should be composed of 6 fields: <market>, <price>, <ask>, <bid>, <change1h>, <change24h>")

    return None


def format_wallet_raw_data(wallet_raw_data: dict) -> Optional[WalletDict]:
    """
    Format market raw data

    :param wallet_raw_data: The wallet raw data
    :return: The formatted data list
    """
    if all(required_field in wallet_raw_data for required_field in ["coin", "total", "free", "availableWithoutBorrow",
                                                                    "usdValue", "spotBorrow"]):
        return {
            "coin": wallet_raw_data["coin"],
            "total": float(wallet_raw_data["total"]),
            "free": float(wallet_raw_data["free"]),
            "availableWithoutBorrow": float(wallet_raw_data["availableWithoutBorrow"]),
            "usdValue": float(wallet_raw_data["usdValue"]),
            "spotBorrow": float(wallet_raw_data["spotBorrow"])
        }
    else:
        logging.warning(
            "Data should be composed of 6 fields: <coin>, <total>, <free>, <availableWithoutBorrow>, <usdValue>, "
            "<spotBorrow>")

    return None

