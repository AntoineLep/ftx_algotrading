import logging
import math
import os
from typing import Optional

from core.enums.side_enum import SideEnum
from core.enums.trigger_order_type_enum import TriggerOrderTypeEnum
from core.models.market_data_dict import MarketDataDict
from core.models.position_data_dict import PositionDataDict
from core.models.raw_stock_data_dict import RawStockDataDict
from core.models.ticker_data_dict import TickerDataDict
from core.models.wallet_dict import WalletDict
from exceptions.ftx_algotrading_exception import FtxAlgotradingException


def expand_var_and_user(path) -> str:
    return os.path.expanduser(os.path.expandvars(path))


def flatten(t):
    return [item for sublist in t for item in sublist]


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
    if all(required_field in market_raw_data for required_field in ["name", "price", "ask", "bid", "change1h",
                                                                    "change24h", "sizeIncrement"]):
        return {
            "name": market_raw_data["name"],
            "price": float(market_raw_data["price"]),
            "ask": float(market_raw_data["ask"]),
            "bid": float(market_raw_data["bid"]),
            "change1h": float(market_raw_data["change1h"]),
            "change24h": float(market_raw_data["change24h"]),
            "size_increment": float(market_raw_data["sizeIncrement"])
        }
    else:
        logging.warning(
            "Data should be composed of 6 fields: <name>, <price>, <ask>, <bid>, <change1h>, <change24h>")

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
            "available_without_borrow": float(wallet_raw_data["availableWithoutBorrow"]),
            "usd_value": float(wallet_raw_data["usdValue"]),
            "spot_borrow": float(wallet_raw_data["spotBorrow"])
        }
    else:
        logging.warning(
            "Data should be composed of 6 fields: <coin>, <total>, <free>, <availableWithoutBorrow>, <usdValue>, "
            "<spotBorrow>")

    return None


def format_position_raw_data(position_raw_data: dict) -> Optional[PositionDataDict]:
    """
    Format position raw data

    :param position_raw_data: The position raw data
    :return: The formatted data list
    """
    if all(required_field in position_raw_data for required_field in ["future", "size", "side", "netSize",
                                                                      "longOrderSize", "shortOrderSize", "cost",
                                                                      "entryPrice", "unrealizedPnl", "realizedPnl",
                                                                      "initialMarginRequirement",
                                                                      "maintenanceMarginRequirement", "openSize",
                                                                      "collateralUsed", "estimatedLiquidationPrice"
                                                                      ]):
        return {
            "future": position_raw_data["future"],
            "size": float(position_raw_data["size"]),
            "side": SideEnum.BUY if position_raw_data["side"] == "buy" else SideEnum.SELL,
            "net_size": float(position_raw_data["netSize"]),
            "long_order_size": float(position_raw_data["longOrderSize"]),
            "short_order_size": float(position_raw_data["shortOrderSize"]),
            "cost": float(position_raw_data["cost"]),
            "entry_price": float(position_raw_data["entryPrice"])
            if position_raw_data["entryPrice"] is not None else None,
            "unrealized_pnl": float(position_raw_data["unrealizedPnl"]),
            "realized_pnl": float(position_raw_data["realizedPnl"]),
            "initial_margin_requirement": float(position_raw_data["initialMarginRequirement"]),
            "maintenance_margin_requirement": float(position_raw_data["maintenanceMarginRequirement"]),
            "open_size": float(position_raw_data["openSize"]),
            "collateral_used": float(position_raw_data["collateralUsed"]),
            "estimated_liquidation_price": float(position_raw_data["estimatedLiquidationPrice"])
            if position_raw_data["estimatedLiquidationPrice"] is not None else None,
        }
    else:
        logging.warning(
            "Data should be composed of 15 fields: <future>, <size>, <side>, <netSize>, <longOrderSize>, "
            "<shortOrderSize>, <cost>, <entryPrice>, <unrealizedPnl>, <realizedPnl>, <initialMarginRequirement>, "
            "<maintenanceMarginRequirement>, <openSize>, <collateralUsed>, <estimatedLiquidationPrice>")

    return None


def get_trigger_order_type(trigger_order_type: TriggerOrderTypeEnum) -> str:
    """
    Get FTX trigger order type for given trigger_order_type enum value

    :param trigger_order_type: trigger_order_type enum value
    :return: FTX trigger order type for given trigger_order_type enum value
    """
    return "trailingStop" if trigger_order_type == TriggerOrderTypeEnum.TRAILING_STOP \
        else "takeProfit" if trigger_order_type == TriggerOrderTypeEnum.TAKE_PROFIT else "stop"


def format_ticker_raw_data(ticker_raw_data: dict) -> Optional[TickerDataDict]:
    """
    Format ticker raw data

    :param ticker_raw_data: The raw data
    :return: The formatted ticker data
    """
    logging.info(ticker_raw_data)
    if all(required_field in ticker_raw_data for required_field in ["bid", "ask", "bidSize", "askSize","last", "time"]):
        return {
            "bid": float(ticker_raw_data["bid"]),
            "ask": float(ticker_raw_data["ask"]),
            "bid_size": float(ticker_raw_data["bidSize"]),
            "ask_size": float(ticker_raw_data["askSize"]),
            "last": float(ticker_raw_data["last"]),
            "time": float(ticker_raw_data["time"]),
        }
    else:
        logging.warning(
            "Data should be composed of 6 fields: <bid>, <ask>, <bidSize>, <askSize>, <last>, <time>")

    return None
