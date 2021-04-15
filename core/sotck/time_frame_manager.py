import logging
import math
import threading
import time

from core.sotck.stock_data_manager import MAX_ITEM_IN_DATA_SET
from core.sotck.stock_data_manager import StockDataManager
from exceptions.ftx_rest_api_exception import FtxRestApiException
from tools.utils import format_raw_data

SUPPORTED_TIME_FRAME_LENGTH = [15, 60, 300, 900, 3600, 14400, 86400]
MAX_RETRY_DELAY = 120


class TimeFrameManager(object):
    """Time frame manager"""

    def __init__(self, time_frame_length, market, ftx_rest_api, lock):
        """
        Time frame manager constructor

        :param time_frame_length: The length of the time frame in seconds
        :type time_frame_length: int
        :param market: Name of the market (ex: BTC-PERP)
        :type market: str
        :param ftx_rest_api: Instance of FtxRestApi
        :type ftx_rest_api: core.ftx.rest.ftx_rest_api.FtxRestApi
        :param lock: The threading lock
        :type lock: threading.Lock
        """
        self.stock_data_manager = StockDataManager()
        self.market = market
        self._time_frame_length = time_frame_length
        self._t_run = True
        self._t = threading.Thread(target=self._worker)
        self._lock = lock
        self._last_retrieved_data_timestamp = math.floor(time.time() - time_frame_length * MAX_ITEM_IN_DATA_SET)
        self._last_acq_size = 0
        self._ftx_rest_api = ftx_rest_api
        """
        :type: core.ftx.rest.ftx_rest_api.FtxRestApi
        """

        logging.info(
            f"Market: {self.market}, time frame: {self._time_frame_length} sec. New time frame manager created!")

    def feed(self) -> None:
        """Feed the stock data managers with new values"""
        response = self._feed()
        self._last_acq_size = len(response)

        logging.debug(
            f"Market: {self.market}, time frame: {self._time_frame_length} sec. "
            f"Last acquisition size: {self._last_acq_size}")

        if self._last_acq_size > 0:
            self.stock_data_manager.update_data([format_raw_data(r, self._time_frame_length) for r in response])
            self._last_retrieved_data_timestamp = max([math.floor(r["time"] / 1000) for r in response])

            logging.debug(f"Market: {self.market}, time frame: {self._time_frame_length} sec. Last received point")
            logging.debug(response[-1])

    def _feed(self) -> [dict]:
        """
        Feed the stock data managers with new values

        :return: A list containing the raw stock data
        :rtype: list
        """

        retry_delay = 5

        while True:
            try:
                logging.info(f"Market: {self.market}, time frame: {self._time_frame_length} sec. Retrieving OHLC data")
                path = f"markets/{self.market}/candles"
                params = {
                    "resolution": self._time_frame_length,
                    "limit": MAX_ITEM_IN_DATA_SET,
                    "start_time": self._last_retrieved_data_timestamp + 1
                }

                response = self._ftx_rest_api.get(path, params)
                return response
            except FtxRestApiException as ftx_rest_api_ex:
                logging.warning(
                    f"Http request failed, trying again in {retry_delay} sec. Details: {str(ftx_rest_api_ex)}")
                time.sleep(retry_delay)
            except KeyError as key_err:
                logging.warning(f"Data format error, trying again in {retry_delay} sec. Details: {str(key_err)}")
                time.sleep(retry_delay)
            finally:
                retry_delay = retry_delay * 2 if retry_delay * 2 < MAX_RETRY_DELAY else MAX_RETRY_DELAY

    def start(self) -> None:
        """Starts the time frame manager (worker)"""
        self._t.start()

    def stop(self) -> None:
        """Stops the time frame manager (worker)"""
        self._t_run = False

    def _worker(self) -> None:
        """Threaded function that retrieve the OHLC data"""

        while self._t_run:
            with self._lock:
                self.feed()

            time_to_sleep = 15 if self._last_acq_size == 0 or self._last_acq_size == MAX_ITEM_IN_DATA_SET \
                else self._time_frame_length

            logging.debug(
                f"Market: {self.market}, time frame: {self._time_frame_length} sec. Next data acquisition in "
                f"{time_to_sleep} sec")
            for i in range(time_to_sleep):
                if self._t_run:
                    time.sleep(1)
                else:
                    break
        logging.debug(
            f"Market: {self.market}, time frame: {self._time_frame_length} sec. "
            f"Ending time frame manager thread for data acquisition."
        )
