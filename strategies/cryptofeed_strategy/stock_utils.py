import math
import time

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
    def get_atr_14(ftx_rest_api: FtxRestApi, pair: str) -> pd.DataFrame:
        """
        Get the atr 14 stockstat indicator

        :param ftx_rest_api: a FTX rest api instance
        :param pair: The pair to get the atr 14 stockstat indicator for
        :return: The atr 14 stockstat indicator
        """
        # Retrieve 20 last candles
        candles = ftx_rest_api.get(f"markets/{pair}-PERP/candles", {
            "resolution": 60,
            "limit": 20,
            "start_time": math.floor(time.time() - 60 * 20)
        })

        candles = [format_ohlcv_raw_data(candle, 60) for candle in candles]
        candles = [Candle(candle["id"], candle["time"], candle["open_price"], candle["high_price"], candle["low_price"],
                          candle["close_price"], candle["volume"]) for candle in candles]

        stock_stat_candles = [{
            "date": candle.time,
            "open": candle.open_price,
            "high": candle.high_price,
            "low": candle.low_price,
            "close": candle.close_price,
            "volume": candle.volume
        } for candle in candles]

        stock_indicators = stockstats.StockDataFrame.retype(pd.DataFrame(stock_stat_candles))
        return stock_indicators["atr_14"]

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
