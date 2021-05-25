from typing import Set, List, Optional

import pandas as pd
import stockstats

from core.models.candle import Candle
from core.models.raw_stock_data_dict import RawStockDataDict

MAX_ITEM_IN_IND_LIST: int = 200
MAX_ITEM_IN_DATA_SET: int = 300


class StockDataManager(object):
    """Stock data manager"""

    def __init__(self, data_list: List[RawStockDataDict] = None):
        """
        Stock data manager constructor

        :param data_list: Data candle list
        """
        self._data_line: Set[Candle] = set()
        self._data_line_cursor: int = -1  # Last candle identifier performed
        self.stock_data_list: List[Candle] = []  # Last candle values
        self.stock_indicators: Optional[stockstats.StockDataFrame] = None

        if data_list is not None:
            self.update_data(data_list)

    def update_data(self, data_list: List[RawStockDataDict]) -> None:
        """
        Update the data line and compute indicators

        :param data_list: The raw data list
        """
        self._update_data_line(data_list)
        self.stock_data_list = self._get_data_line()

        if len(self.stock_data_list) > 0:
            if self._data_line_cursor == -1:
                # Put the cursor at the position just before the first candle
                self._data_line_cursor = self.stock_data_list[0].identifier - 1

            self._compute_indicators()

        if len(self.stock_data_list) > MAX_ITEM_IN_IND_LIST:
            self.stock_data_list = self.stock_data_list[-MAX_ITEM_IN_IND_LIST:]

        if len(self._data_line) > MAX_ITEM_IN_DATA_SET:
            self._data_line = set(self._get_data_line()[-MAX_ITEM_IN_DATA_SET:])

        self._data_line_cursor = self.stock_data_list[-1].identifier  # Update the cursor position

    def _update_data_line(self, data_list: List[RawStockDataDict]) -> None:
        """
        Update the data line

        :param data_list: The raw data list
        """
        if data_list is not None:
            for data in data_list:
                self._data_line.add(
                    Candle(data["id"], data["time"], data["open_price"], data["high_price"], data["low_price"],
                           data["close_price"], data["volume"])
                )

    def _compute_indicators(self) -> None:
        """Compute indicators"""

        data_line_dict_list = [{
            "date": data_item.time,
            "open": data_item.open_price,
            "high": data_item.high_price,
            "low": data_item.low_price,
            "close": data_item.close_price,
            "volume": data_item.volume
        } for data_item in self.stock_data_list]

        self.stock_indicators = stockstats.StockDataFrame.retype(pd.DataFrame(data_line_dict_list))

    def _get_data_line(self) -> List[Candle]:
        """
        Return the data line sorted by identifier asc

        :return: The data line sorted by identifier asc
        """
        return sorted(self._data_line, key=lambda k: k.identifier)
