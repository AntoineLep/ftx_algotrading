import logging
import math
import threading
import time
from typing import Optional

from core.enums.position_state_enum import PositionStateEnum
from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.models.market_data_dict import MarketDataDict
from core.models.wallet_dict import WalletDict
from tools.utils import format_market_raw_data, format_wallet_raw_data

SUB_POSITION_MAX_PRICE = 10000
POSITION_MAX_PRICE = 250000
_WORKER_SLEEP_TIME_BETWEEN_LOOPS = 5


class PositionDriver(object):
    """Position driver"""

    def __init__(self, ftx_rest_api: FtxRestApi, sub_position_max_price: int = SUB_POSITION_MAX_PRICE,
                 position_max_price: int = POSITION_MAX_PRICE):
        """
        Position driver constructor

        :param ftx_rest_api: Instance of FtxRestApi
        :param sub_position_max_price: Maximum price of a position before having to split it into smaller ones
        :param position_max_price: Maximum price the position driver can drive
        """
        self.ftx_rest_api: FtxRestApi = ftx_rest_api
        self.market: str = ""
        self.position_state: PositionStateEnum = PositionStateEnum.NOT_OPENED
        self.position_size: int = 0
        self._t_run: bool = True
        self._t: Optional[threading.Thread] = None
        self._last_market_data: Optional[MarketDataDict] = None
        self._sub_position_max_price = sub_position_max_price
        self._position_max_price = position_max_price
        logging.debug(f"New position driver created!")

    def open_position(self, market: str, leverage: int, tp_target_percentage: float, sl_target_percentage: float,
                      max_open_duration: int) -> None:
        """
        Open a position using account wallet free usd wallet amount

        :param market: The market pair to use. Ex: BTC-PERP
        :param leverage: Leverage to use
        :param tp_target_percentage: Take profit after the price has reached a given percentage of value
        :param sl_target_percentage: Stop loss after the price has loosed a given percentage of value
        :param max_open_duration: Close the order regardless of the market after a max open duration
        """

        if self.position_state == PositionStateEnum.NOT_OPENED:
            response = self.ftx_rest_api.get("wallet/balances")
            wallets = [wallet for wallet in response if wallet["coin"] == 'USD' and wallet["free"] >= 10]

            if len(wallets) == 1:
                wallet: WalletDict = format_wallet_raw_data(wallets[0])
                position_price = min(math.floor(wallet["free"]) * leverage, self._position_max_price)
                self.position_size = 0
                self.market = market

                # Store market data before opening a position to compute position size, TP and SL
                logging.info("Retrieving market price")
                response = self.ftx_rest_api.get(f"markets/{self.market}")
                logging.info(f"FTX API response: {str(response)}")
                self._last_market_data = format_market_raw_data(response)

                while position_price > 1:
                    sub_position_price = position_price if position_price < self._sub_position_max_price \
                        else self._sub_position_max_price
                    sub_position_size = math.floor(sub_position_price / self._last_market_data["ask"])

                    order_params = {
                        "market": self.market,
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

        last_market_price = self._last_market_data["price"]
        tp_price = self._last_market_data["price"] + self._last_market_data["price"] * tp_target_percentage / 100
        sl_price = self._last_market_data["price"] - self._last_market_data["price"] * sl_target_percentage / 100
        opened_duration = 0

        while self._t_run:
            for i in range(_WORKER_SLEEP_TIME_BETWEEN_LOOPS):
                if self._t_run:
                    time.sleep(1)
                    opened_duration += 1
                else:
                    break

            # Update market price
            logging.info("Retrieving market price")
            response = self.ftx_rest_api.get(f"markets/{self.market}")
            logging.info(f"FTX API response: {str(response)}")
            self._last_market_data = format_market_raw_data(response)

            if self._last_market_data is not None and last_market_price != self._last_market_data["price"]:
                last_market_price = self._last_market_data["price"]

                logging.info("Checking position close condition:")
                logging.info(f"Current price is {self._last_market_data['price']}")
                logging.info(f"TP price is {tp_price}")
                logging.info(f"SL price is {sl_price}")
                logging.info(f"Order opened duration is {opened_duration}")

                if last_market_price >= tp_price:
                    logging.info("TP price reached  !! =D")
                if last_market_price <= sl_price:
                    logging.info("SL price reached. :'(")
                if opened_duration > max_open_duration:
                    logging.info("Max open duration reached ! :)")

                # New market price: Check if close condition are respected:
                # Position has reached target
                # Position is losing too much value
                # Position has reached max open duration
                if last_market_price >= tp_price or last_market_price <= sl_price or \
                        opened_duration >= max_open_duration:
                    order_params = {
                        "market": self.market,
                        "side": "sell",
                        "price": None,
                        "type": "market",
                        "size": self.position_size,
                        "reduceOnly": True
                    }

                    logging.info(f"Closing position: {str(order_params)}")

                    try:
                        response = self.ftx_rest_api.post("orders", order_params)
                        logging.info(f"FTX API response: {str(response)}")
                    except Exception as e:
                        logging.error("An error occurred when opening position:")
                        logging.error(e)

                    # Order has been closed, we can reset the driver and break the thread loop
                    self._reset_driver()
                    break
