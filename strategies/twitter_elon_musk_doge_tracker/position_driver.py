import logging
import math
import threading
import time

from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.sotck.stock_data_manager import StockDataManager
from strategies.twitter_elon_musk_doge_tracker.enums.position_state_enum import PositionStateEnum

LEVERAGE = 1


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
        self._t: threading.Thread = threading.Thread(target=self._worker)
        self._lock = lock
        logging.debug(f"New position driver created!")

    def open_position(self):
        """Open a position using account wallet free usd wallet amount"""

        if self.position_state == PositionStateEnum.NOT_OPENED:
            with self._lock:
                response = self.ftx_rest_api.get("wallet/balances")
                wallet = [wallet for wallet in response if wallet["coin"] == 'USD' and wallet["free"] >= 10]
                if len(wallet) == 1:
                    wallet = wallet[0]
                    position_price = math.floor(wallet["free"]) * LEVERAGE
                    position_price = 1  # TODO: remove this after testing

                    last_data_point = self.stock_data_manager.stock_data_list[-1]
                    self.position_size = math.floor(position_price / last_data_point.close_price)

                    order_params = {
                        "market": "DOGE-PERP",
                        "side": "buy",
                        "price": None,
                        "type": "market",
                        "size": self.position_size
                    }
                    logging.info(f"Opening position: {str(order_params)}")
                    # self.ftx_rest_api.post("orders", order_params)
                else:
                    return

    def _worker(self) -> None:
        """Threaded function that drive the opened position"""

        while self._t_run:
            for i in range(10):
                if self._t_run:
                    time.sleep(1)
                else:
                    break
