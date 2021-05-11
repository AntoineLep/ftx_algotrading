from typing import List

from core.models.raw_stock_data_dict import RawStockDataDict
from core.stock.time_frame_manager import TimeFrameManager


class MockedCandleInjector(object):
    """Mocked candle injector"""

    def __init__(self, time_frame_manager: TimeFrameManager, pending_data: List[RawStockDataDict] = None,
                 initial_data: List[RawStockDataDict] = None):
        """
        Stock data manager constructor

        :param time_frame_manager: Time frame manager to mock data into
        :param pending_data: Data waiting to be injected within the time frame
        :param initial_data: Initial data candles to inject within the time frame
        """
        self.time_frame_manager = time_frame_manager
        self.pending_data = pending_data

        if initial_data is not None:
            self.time_frame_manager.stock_data_manager.update_data(initial_data)

    def tick(self, next_candle: RawStockDataDict = None) -> None:
        """
        Simulate a stock data reception injecting a candle within the managed time frame

        :param next_candle: Next candle to be injected. Will use the pending_data if None
        """
        if next_candle is None and len(self.pending_data) > 0:
            next_candle = self.pending_data.pop()

        if next_candle is not None:
            self.time_frame_manager.stock_data_manager.update_data([next_candle])
