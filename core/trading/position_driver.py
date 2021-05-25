import logging
import threading
import time
from typing import Optional

from core.enums.order_side_enum import OrderSideEnum
from core.enums.order_type_enum import OrderTypeEnum
from core.enums.position_state_enum import PositionStateEnum
from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.models.position_config_dict import PositionConfigDict
from tools.utils import get_trigger_order_type

_WORKER_SLEEP_TIME_BETWEEN_LOOPS = 10


class PositionDriver(object):
    """Position driver"""

    def __init__(self, ftx_rest_api: FtxRestApi):
        """
        Position driver constructor

        :param ftx_rest_api: Instance of FtxRestApi
        """
        self.ftx_rest_api: FtxRestApi = ftx_rest_api
        self.market: str = ""
        self.position_state: PositionStateEnum = PositionStateEnum.NOT_OPENED
        self.position_size: int = 0
        self.position_side: Optional[OrderSideEnum] = None
        self._t_run: bool = True
        self._t: Optional[threading.Thread] = None
        logging.debug(f"New position driver created!")

    def open_position(self, market: str, side: OrderSideEnum, position_config: PositionConfigDict) -> None:
        """
        Open a position using account wallet free usd wallet amount

        :param market: The market pair to use. Ex: BTC-PERP
        :param side: The side of the position to open
        :param position_config: Position configuration
        """

        if self.position_state == PositionStateEnum.NOT_OPENED and (self._t is None or self._t.is_alive() is False):
            self.market = market
            self.position_side = side
            self.position_size = 0

            # Open positions
            for opening in position_config["openings"]:

                order_params = {
                    "market": self.market,
                    "side": "buy" if self.position_side == OrderSideEnum.BUY else "sell",
                    "price": opening["price"],
                    "type": "market" if opening["type"] == OrderTypeEnum.MARKET else "limit",
                    "size": opening["size"]
                }

                logging.info(f"Opening position: {str(order_params)}")
                try:
                    response = self.ftx_rest_api.post("orders", order_params)
                    logging.info(f"FTX API response: {str(response)}")
                    self.position_size += opening["size"]
                    time.sleep(0.25)
                except Exception as e:
                    logging.error("An error occurred when opening position:")
                    logging.error(e)

            # Apply trigger orders
            for trigger_order in position_config["trigger_orders"]:

                trigger_order_params = {
                    "market": self.market,
                    "side": "sell" if self.position_side == OrderSideEnum.BUY else "buy",
                    "size": trigger_order["size"],
                    "type": get_trigger_order_type(trigger_order["type"]),
                    "reduceOnly": trigger_order["reduce_only"],
                    "triggerPrice": trigger_order["trigger_price"],
                    "orderPrice": trigger_order["order_price"],
                    "trailValue": trigger_order["trail_value"]
                }

                logging.info(f"Opening trigger order: {str(trigger_order_params)}")
                try:
                    response = self.ftx_rest_api.post("conditional_orders", trigger_order_params)
                    logging.info(f"FTX API response: {str(response)}")
                    time.sleep(0.25)
                except Exception as e:
                    logging.error("An error occurred when opening position:")
                    logging.error(e)

            self.position_state = PositionStateEnum.OPENED
            self._watch_market(position_config["max_open_duration"])
        else:
            return

    def close_position_and_cancel_orders(self) -> None:
        if self.position_state == PositionStateEnum.OPENED:
            order_params = {
                "market": self.market,
                "side": "sell" if self.position_side == OrderSideEnum.BUY else "buy",
                "price": None,
                "type": "market",
                "size": self.position_size
            }

            try:
                logging.info(f"Closing position: {str(order_params)}")
                response = self.ftx_rest_api.post("orders", order_params)
                logging.info(f"FTX API response: {str(response)}")
            except Exception as e:
                logging.error("An error occurred when closing position:")
                logging.error(e)

                time.sleep(0.25)

            try:
                logging.info(f"Canceling all orders")
                response = self.ftx_rest_api.delete("orders", order_params)
                logging.info(f"FTX API response: {str(response)}")
            except Exception as e:
                logging.error("An error occurred when cancelling orders:")
                logging.error(e)

            self._reset_driver()

    def _watch_market(self, max_open_duration: int):
        """
        Start to watch the market

        :param max_open_duration: Close the order regardless of the market after a max open duration"""

        self._t_run = True
        self._t = threading.Thread(target=self._worker, args=[max_open_duration])
        self._t.start()

    def _reset_driver(self):
        """Reset the worker"""

        self._t_run = False
        self.position_state = PositionStateEnum.NOT_OPENED

    def _worker(self, max_open_duration: int) -> None:
        """
        Threaded function that drive the opened position

        :param max_open_duration: Close the order regardless of the market after a max open duration
        """

        opened_duration = 0

        while self._t_run:
            for i in range(_WORKER_SLEEP_TIME_BETWEEN_LOOPS):
                if self._t_run:
                    time.sleep(1)
                    opened_duration += 1
                else:
                    break

            # Update market price
            logging.info("Retrieving orders")
            response = self.ftx_rest_api.get("conditional_orders", {"market": self.market})
            [logging.info(f"FTX API response: {str(resp)}") for resp in response]

            logging.info("Checking position close condition:")
            logging.info(f"Order opened duration is {opened_duration}")

            if opened_duration > max_open_duration:
                logging.info("Max open duration reached !")

            if opened_duration >= max_open_duration:
                self.close_position_and_cancel_orders()
                break
