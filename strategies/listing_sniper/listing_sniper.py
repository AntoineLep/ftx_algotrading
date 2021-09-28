import logging
import time
import math

from core.strategy.strategy import Strategy
from core.ftx.ws.ftx_websocket_client import FtxWebsocketClient
from core.ftx.rest.ftx_rest_api import FtxRestApi


class ListingSniper(Strategy):
    """Listing Sniper"""

    def __init__(self):
        """The listing sniper strategy constructor"""

        logging.info("ListingSniper run strategy")
        super(ListingSniper, self).__init__()

        self.cpt = 1
        self._sniped = False
        self.market: str = "BLT/USD"
        self.invest_amount = 800  # USD amount to invest on the coin as listed
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
            response = self.ftx_rest_api.get("markets/" + self.market)
            logging.info(f"FTX API response: {str(response)}")

            market_enabled = response["enabled"]
            logging.info(f"market enabled: {str(market_enabled)}")

            if market_enabled is False:
                raise Exception(f"Market {str(self.market)} is not enabled yet")

            order_size = math.floor(self.invest_amount / response["ask"])

            order_params = {
                "market": self.market,
                "side": "buy",
                "price": None,
                "type": "market",
                "size": order_size
            }

            if self.cpt < 5:
                raise Exception("waiting a bit")

            try:
                logging.info(f"Opening position: {str(order_params)}")
                response = self.ftx_rest_api.post("orders", order_params)
                logging.info(f"FTX API response: {str(response)}")

                self._sniped = True
                logging.info(f"Sniping done !")
            except Exception as e:
                logging.error("An error occurred when opening position:")
                logging.error(e)

        except Exception as e:
            logging.error(e)

    def after_loop(self) -> None:
        time.sleep(10)
        self.cpt += 1

    def cleanup(self) -> None:
        """Clean strategy execution"""
        logging.info("ListingSniper cleanup")
