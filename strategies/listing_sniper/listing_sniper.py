import logging
import time
import math

from core.strategy.strategy import Strategy
from core.ftx.ws.ftx_websocket_client import FtxWebsocketClient
from core.ftx.rest.ftx_rest_api import FtxRestApi

# Trading pair to snipe
MARKET_PAIR_TO_SNIPE = "CTX/USD"

# USD amount to invest on the coin to be listed
# /!\ Make sure your wallet have more (twice is good) than this amount because due to the high demand,
# the order fill price can be higher than the computed one based on last stock data
AMOUNT_TO_INVEST = 1500

# Minimum size increment to compute order size
# Ensure your order size will be a multiple of the size increment value
SIZE_INCREMENT = 10


class ListingSniper(Strategy):
    """Listing Sniper"""

    def __init__(self):
        """The listing sniper strategy constructor"""

        logging.info("ListingSniper run strategy")
        super(ListingSniper, self).__init__()

        self._sniped = False
        self.ftx_ws_client: FtxWebsocketClient = FtxWebsocketClient()
        self.ftx_ws_client.connect()
        self.ftx_rest_api: FtxRestApi = FtxRestApi()

    def before_loop(self) -> None:
        pass

    def loop(self) -> None:
        """The strategy core"""
        if self._sniped:
            return

        try:
            response = self.ftx_rest_api.get("markets/" + MARKET_PAIR_TO_SNIPE)
            logging.info(f"FTX API response: {str(response)}")

            market_enabled = response["enabled"]
            logging.info(f"market enabled: {str(market_enabled)}")

            if market_enabled is False:
                raise Exception(f"Market {MARKET_PAIR_TO_SNIPE} is not yet enabled")

            order_size = math.floor(AMOUNT_TO_INVEST / response["ask"]) - \
                math.floor(AMOUNT_TO_INVEST / response["ask"]) % SIZE_INCREMENT

            order_params = {
                "market": MARKET_PAIR_TO_SNIPE,
                "side": "buy",
                "price": None,
                "type": "market",
                "size": order_size,
                "ioc": False
            }

            try:
                logging.info(f"Opening position: {str(order_params)}")
                response = self.ftx_rest_api.post("orders", order_params)
                logging.info(f"FTX API response: {str(response)}")

                self._sniped = True
                logging.info(f"Sniping done !")
            except Exception as e:
                logging.error("An error occurred when opening position:")
                logging.error(e)
                raise

        except Exception as e:
            logging.error(e)

    def after_loop(self) -> None:
        time.sleep(10)

    def cleanup(self) -> None:
        """Clean strategy execution"""
        logging.info("ListingSniper cleanup")
