import logging
import math
import threading
import time

from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.stock.stock_data_manager import MAX_ITEM_IN_DATA_SET
from core.stock.stock_data_manager import StockDataManager
from exceptions.ftx_rest_api_exception import FtxRestApiException
from tools.utils import format_ohlcv_raw_data

SUPPORTED_TIME_FRAME_LENGTH = [15, 60, 300, 900, 3600, 14400, 86400]
MAX_RETRY_DELAY = 120


class TimeFrameManager(object):
    """Time frame manager"""

    log_received_stock_data = True

    def __init__(self, time_frame_length: int, market: str, ftx_rest_api: FtxRestApi,
                 auto_compute_indicators: bool = True):
        """
        Time frame manager constructor

        :param time_frame_length: The length of the time frame in seconds
        :param market: Name of the market (ex: BTC-PERP)
        :param ftx_rest_api: Instance of FtxRestApi
        :param auto_compute_indicators: automatically compute indicators or not
        """
        self.stock_data_manager: StockDataManager = StockDataManager(auto_compute_indicators=auto_compute_indicators)
        self.market: str = market
        self._time_frame_length: int = time_frame_length
        self._t_run: bool = True
        self._t: threading.Thread = threading.Thread(target=self._worker)
        self._last_retrieved_data_timestamp: int = math.floor(time.time() - time_frame_length * MAX_ITEM_IN_DATA_SET)
        self._last_acq_size: int = 0
        self._ftx_rest_api: FtxRestApi = ftx_rest_api

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
            self.stock_data_manager.update_data([format_ohlcv_raw_data(r, self._time_frame_length) for r in response])
            self._last_retrieved_data_timestamp = max([math.floor(r["time"] / 1000) for r in response])

            if TimeFrameManager.log_received_stock_data:
                logging.info(f"Market: {self.market}, time frame: {self._time_frame_length} sec. Last received point")
                logging.info(response[-1])

    def _feed(self) -> [dict]:
        """
        Feed the stock data managers with new values

        :return: A list containing the raw stock data
        """
        retry_delay = 5

        while True:
            try:
                logging.debug(f"Market: {self.market}, time frame: {self._time_frame_length} sec. Retrieving OHLC data")

                return self._ftx_rest_api.get(f"markets/{self.market}/candles", {
                    "resolution": self._time_frame_length,
                    "limit": MAX_ITEM_IN_DATA_SET,
                    "start_time": self._last_retrieved_data_timestamp + 1
                })

            except FtxRestApiException as ftx_rest_api_ex:
                logging.error(
                    f"FTX API: Http request failed, trying again in {retry_delay} sec. Details: {str(ftx_rest_api_ex)}")
                time.sleep(retry_delay)
            except KeyError as key_err:
                logging.error(f"FTX API: Data format error, trying again in {retry_delay} sec. Details: {str(key_err)}")
                time.sleep(retry_delay)
            except Exception as e:
                logging.error(f"FTX API: Unknown error, trying again in {retry_delay} sec. Details: {str(e)}")
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
