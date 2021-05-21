import logging
import math
import threading
import time
from typing import Optional

from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.models.candle import Candle
from core.stock.stock_data_manager import StockDataManager
from strategies.twitter_elon_musk_doge_tracker.enums.position_state_enum import PositionStateEnum


SUB_POSITION_MAX_PRICE = 2


class PositionDriver(object):
    """Position driver"""

    def __init__(self, ftx_rest_api: FtxRestApi, stock_data_manager: StockDataManager, lock: threading.Lock):
        """
        Position driver constructor

        :param ftx_rest_api: Instance of FtxRestApi
        """
        self.ftx_rest_api: FtxRestApi = ftx_rest_api
        self.stock_data_manager: StockDataManager = stock_data_manager
        self.position_state: PositionStateEnum = PositionStateEnum.NOT_OPENED
        self.position_size: int = 0
        self._t_run: bool = True
        self._t: Optional[threading.Thread] = None
        self._lock: threading.Lock = lock
        self._last_data_candle: Optional[Candle] = None
        logging.debug(f"New position driver created!")

    def open_position(self, leverage: int, tp_target_percentage: float, sl_target_percentage: float,
                      max_open_duration: int) -> None:
        """
        Open a position using account wallet free usd wallet amount

        :param leverage: Leverage to use
        :param tp_target_percentage: Take profit after the price has reached a given percentage of value
        :param sl_target_percentage: Stop loss after the price has loosed a given percentage of value
        :param max_open_duration: Close the order regardless of the market after a max open duration
        """

        if self.position_state == PositionStateEnum.NOT_OPENED:
            with self._lock:
                response = self.ftx_rest_api.get("wallet/balances")
                wallet = [wallet for wallet in response if wallet["coin"] == 'USD' and wallet["free"] >= 10]
                if len(wallet) == 1:
                    wallet = wallet[0]
                    position_price = 10  # min(math.floor(wallet["free"]) * leverage, 250000)
                    self.position_size = 0
                    self._last_data_candle = self.stock_data_manager.stock_data_list[-1]

                    while position_price > 1:
                        sub_position_price = position_price if position_price < SUB_POSITION_MAX_PRICE \
                            else SUB_POSITION_MAX_PRICE
                        sub_position_size = math.floor(sub_position_price / self._last_data_candle.close_price)

                        order_params = {
                            "market": "DOGE-PERP",
                            "side": "buy",
                            "price": None,
                            "type": "market",
                            "size": sub_position_size
                        }

                        if self._t is None or self._t.is_alive() is False:
                            logging.info(f"Opening position: {str(order_params)}")
                            try:
                                response = self.ftx_rest_api.post("orders", order_params)
                                logging.info(f"FTX API response: {str(response)}")
                                self.position_size += sub_position_size
                                time.sleep(0.25)
                            except Exception as e:
                                logging.error("An error occurred when opening position:")
                                logging.error(e)

                        position_price -= sub_position_price

                    if self._t is None or self._t.is_alive() is False:
                        self.position_state = PositionStateEnum.OPENED
                        self._watch_market(tp_target_percentage, sl_target_percentage, max_open_duration)
                else:
                    return

    def _watch_market(self, tp_target_percentage: float, sl_target_percentage: float, max_open_duration: int):
        """
        Start to watch the market

        :param tp_target_percentage: Take profit after the price has reached a given percentage of value
        :param sl_target_percentage: Stop loss after the price has loosed a given percentage of value
        :param max_open_duration: Close the order regardless of the market after a max open duration"""

        self._t_run = True
        self._t = threading.Thread(target=self._worker,
                                   args=[tp_target_percentage, sl_target_percentage, max_open_duration])
        self._t.start()

    def _reset_driver(self):
        """Reset the worker"""

        self._t_run = False
        self.position_state = PositionStateEnum.NOT_OPENED

    def _worker(self, tp_target_percentage: int, sl_target_percentage: int, max_open_duration: int) -> None:
        """
        Threaded function that drive the opened position

        :param tp_target_percentage: Take profit after the price has reached a given percentage of value
        :param sl_target_percentage: Stop loss after the price has loosed a given percentage of value
        :param max_open_duration: Close the order regardless of the market after a max open duration
        """

        last_data_candle_identifier = self._last_data_candle.identifier
        tp_price = self._last_data_candle.close_price + self._last_data_candle.close_price * tp_target_percentage / 100
        sl_price = self._last_data_candle.close_price - self._last_data_candle.close_price * sl_target_percentage / 100
        opened_duration = 0

        while self._t_run:
            self._last_data_candle = self.stock_data_manager.stock_data_list[-1]

            if last_data_candle_identifier != self._last_data_candle.identifier:
                last_data_candle_identifier = self._last_data_candle.identifier

                logging.info("Checking position close condition:")
                logging.info(f"Current price is {self._last_data_candle.close_price}")
                logging.info(f"TP price is {tp_price}")
                logging.info(f"SL price is {sl_price}")
                logging.info(f"Order opened duration is {opened_duration}")

                if self._last_data_candle.close_price >= tp_price:
                    logging.info("TP price reached  !! =D")
                if self._last_data_candle.close_price <= sl_price:
                    logging.info("SL price reached. :'(")
                if opened_duration > max_open_duration:
                    logging.info("Max open duration reached ! :)")

                # New data candle: Check if close condition are respected:
                # Position has reached target
                # Position is losing too much value
                # Position has reached max open duration
                if self._last_data_candle.close_price >= tp_price or self._last_data_candle.close_price <= sl_price or \
                        opened_duration >= max_open_duration:
                    order_params = {
                        "market": "DOGE-PERP",
                        "side": "sell",
                        "price": None,
                        "type": "market",
                        "size": self.position_size,
                        "reduceOnly": True
                    }

                    logging.info(f"Closing position: {str(order_params)}")

                    with self._lock:
                        try:
                            response = self.ftx_rest_api.post("orders", order_params)
                            logging.info(f"FTX API response: {str(response)}")
                        except Exception as e:
                            logging.error("An error occurred when opening position:")
                            logging.error(e)

                    # Order has been closed, we can reset the driver
                    self._reset_driver()
                    break

            for i in range(5):
                if self._t_run:
                    time.sleep(1)
                    opened_duration += 1
                else:
                    break
