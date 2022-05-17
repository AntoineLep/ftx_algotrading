import math
import time
from typing import List, Tuple

import pandas as pd
import stockstats

from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.models.candle import Candle
from core.models.market_data_dict import MarketDataDict
from tools.utils import format_wallet_raw_data, format_market_raw_data, format_ohlcv_raw_data


class StockUtils(object):

    @staticmethod
    def get_market_price(ftx_rest_api: FtxRestApi, pair: str) -> float:
        """
        Retrieve the market price for a given pair

        :param ftx_rest_api: a FTX rest api instance
        :param pair: The pair to retrieve market price for
        :return: The market price of the given pair
        """
        response = ftx_rest_api.get(f"markets/{pair}")
        market_data: MarketDataDict = format_market_raw_data(response)
        return market_data.get("price")

    @staticmethod
    def get_last_x_stockstats_candles(ftx_rest_api: FtxRestApi, pair: str, x: int) -> List:
        """
        Get the last x stockstats candles indicator

        :param ftx_rest_api: a FTX rest api instance
        :param pair: The pair to get the candles for
        :param x: The number of candles to get
        :return: The last x stockstats candles
        """
        # Retrieve x last candles
        candles = ftx_rest_api.get(f"markets/{pair}-PERP/candles", {
            "resolution": 60,
            "limit": x,
            "start_time": math.floor(time.time() - 60 * x)
        })

        candles = [format_ohlcv_raw_data(candle, 60) for candle in candles]
        candles = [Candle(candle["id"], candle["time"], candle["open_price"], candle["high_price"], candle["low_price"],
                          candle["close_price"], candle["volume"]) for candle in candles]

        return [{
            "date": candle.time,
            "open": candle.open_price,
            "high": candle.high_price,
            "low": candle.low_price,
            "close": candle.close_price,
            "volume": candle.volume
        } for candle in candles]

    @staticmethod
    def get_atr_14(stock_stat_candles: List) -> pd.DataFrame:
        """
        Get the atr 14 stockstats indicator

        :param stock_stat_candles: The candles to compute atr for
        :return: The atr 14 stockstats indicator
        """

        stock_indicators = stockstats.StockDataFrame.retype(pd.DataFrame(stock_stat_candles))
        return stock_indicators["atr_14"]

    @staticmethod
    def get_bollinger_bands(stock_stat_candles: List) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get the Bollinger bands (up, down) stockstats indicator

        :param stock_stat_candles: The candles to compute atr for
        :return: The Bollinger bands (up, down) stockstats indicators
        """

        stock_indicators = stockstats.StockDataFrame.retype(pd.DataFrame(stock_stat_candles))
        return stock_indicators["boll_ub"], stock_indicators["boll_lb"]

    @staticmethod
    def get_available_balance_without_borrow(ftx_rest_api: FtxRestApi) -> float:
        """
        Retrieve the usd available balance without borrow

        :param ftx_rest_api: a FTX rest api instance
        :return: The usd available balance without borrow
        """
        response = ftx_rest_api.get("wallet/balances")
        wallets = [format_wallet_raw_data(wallet) for wallet in response if wallet["coin"] == 'USD']

        return wallets[0]["available_without_borrow"]
