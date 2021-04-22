import pandas as pd
import stockstats
from typing import Set, List, Optional

from core.models.stock_data_point import StockDataPoint

MAX_ITEM_IN_IND_LIST: int = 200
MAX_ITEM_IN_DATA_SET: int = 300


class StockDataManager(object):
    """Stock data manager"""

    def __init__(self, data_list=None):
        """
        Stock data manager constructor

        :param data_list: Data point list
        :type data_list: list
        """
        self._data_line: Set[StockDataPoint] = set()
        self._data_line_cursor: int = -1  # Last data identifier performed
        self.stock_data_list: List[StockDataPoint] = []  # Last raw stock values
        self.stock_indicators: Optional[stockstats.StockDataFrame] = None

        if data_list is not None:
            self.update_data(data_list)

    def update_data(self, data_list: list) -> None:
        """
        Update the data line and compute indicators

        :param data_list: The raw data list
        """
        self._update_data_line(data_list)
        self.stock_data_list = self._get_data_line()

        if len(self.stock_data_list) > 0:
            if self._data_line_cursor == -1:
                # Put the cursor at the position just before the first data point
                self._data_line_cursor = self.stock_data_list[0].identifier - 1

            self._compute_indicators()

        if len(self.stock_data_list) > MAX_ITEM_IN_IND_LIST:
            self.stock_data_list = self.stock_data_list[-MAX_ITEM_IN_IND_LIST:]

        if len(self._data_line) > MAX_ITEM_IN_DATA_SET:
            self._data_line = set(self._get_data_line()[-MAX_ITEM_IN_DATA_SET:])

        self._data_line_cursor = self.stock_data_list[-1].identifier  # Update the cursor position

    def _update_data_line(self, data_list: list) -> None:
        """
        Update the data line

        :param data_list: The raw data list
        :type data_list: list
        """
        if data_list is not None:
            for data in data_list:
                self._data_line.add(
                    StockDataPoint(data["id"], data["time"], data["open"], data["high"], data["low"], data["close"],
                                   data["volume"])
                )

    def _compute_indicators(self) -> None:
        """Compute indicators"""

        data_line_dict_list = [{
            "date": data_item.time,
            "close": data_item.close_price,
            "high": data_item.high_price,
            "low": data_item.low_price,
            "open": data_item.open_price,
            "volume": data_item.volume
        } for data_item in self.stock_data_list]

        self.stock_indicators = stockstats.StockDataFrame.retype(pd.DataFrame(data_line_dict_list))

    def _get_data_line(self) -> List[StockDataPoint]:
        """
        Return the data line sorted by identifier asc

        :return: The data line sorted by identifier asc
        :rtype: list
        """
        return sorted(self._data_line, key=lambda k: k.identifier)
