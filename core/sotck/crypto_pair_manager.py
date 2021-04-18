import logging
import threading

from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.sotck.time_frame_manager import TimeFrameManager
from exceptions.ftx_algotrading_exception import FtxAlgotradingException

SUPPORTED_TIME_FRAME_LENGTH = [15, 60, 300, 900, 3600, 14400, 86400]


class CryptoPairManager(object):
    """Crypto pair manager"""

    def __init__(self, market: str, ftx_rest_api: FtxRestApi, lock: threading.Lock):
        """
        Crypto pair manager constructor

        :param market: Name of the currency to trade with
        :param ftx_rest_api: Instance of FtxRestApi
        :param lock: The threading lock
        """
        self.market = market
        self._time_frames = {}
        self._ftx_rest_api = ftx_rest_api
        self._lock = lock
        logging.info(f"New crypto pair manager created! Market: {self.market}")

    def add_time_frame(self, time_frame_length: int) -> None:
        """
        Add a new time frame

        :param time_frame_length: The length of the time frame in seconds (15, 60, 300, 900, 3600, 14400, 86400)
        """
        if time_frame_length not in SUPPORTED_TIME_FRAME_LENGTH:
            raise FtxAlgotradingException(
                f"Time frame length must be one of the following: "
                f"{', '.join([str(item) for item in SUPPORTED_TIME_FRAME_LENGTH])} ")

        if time_frame_length in self._time_frames:
            logging.warning(f"Time frame length ({time_frame_length}) is already managed for market {self.market}")
            return

        self._time_frames[time_frame_length] = TimeFrameManager(time_frame_length, self.market, self._ftx_rest_api,
                                                                self._lock)

    def start_time_frame_acq(self, time_frame_length: int) -> None:
        """
        Starts the data acquisition for a given time frame

        :param time_frame_length: The given time frame
        """
        if time_frame_length not in self._time_frames:
            raise FtxAlgotradingException(
                f"Trying to start a non existing time frame {time_frame_length} for market {self.market}")

        self._time_frames[time_frame_length].start()

    def start_all_time_frame_acq(self) -> None:
        """Starts the data acquisition for all time frames"""
        for key in self._time_frames.keys():
            self.start_time_frame_acq(key)

    def stop_time_frame_acq(self, time_frame_length: int) -> None:
        """
        Stops the data acquisition for a given time frame

        :param time_frame_length: The given time frame
        """
        if time_frame_length not in self._time_frames:
            raise FtxAlgotradingException(
                f"Trying to stop a non existing time frame {time_frame_length} for market {self.market}")

        self._time_frames[time_frame_length].stop()

    def stop_all_time_frame_acq(self):
        """Stops the data acquisition for all time frames"""
        for key in self._time_frames.keys():
            self.stop_time_frame_acq(key)

    def get_time_frame(self, time_frame_length: int) -> TimeFrameManager:
        """
        Return the given time frame instance|

        :param time_frame_length: The given time frame
        :return: The given time frame instance
        """
        if time_frame_length not in self._time_frames:
            raise FtxAlgotradingException(
                f"Trying to access a non existing time frame {time_frame_length} for market {self.market}")

        return self._time_frames[time_frame_length]
