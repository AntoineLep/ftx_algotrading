import logging
import time

from core.strategy.strategy import Strategy
from core.ftx.ws.ftx_websocket_client import FtxWebsocketClient
from core.ftx.rest.ftx_rest_api import FtxRestApi


class BestStrategyEver(Strategy):
    """The best strategy ever"""

    def __init__(self):
        """The best strategy ever constructor"""

        logging.info("BestStrategyEver run strategy")
        super(BestStrategyEver, self).__init__()

        self.ftx_ws_client: FtxWebsocketClient = FtxWebsocketClient()
        self.ftx_ws_client.connect()
        self.ftx_rest_api: FtxRestApi = FtxRestApi()

    def before_loop(self) -> None:
        pass

    def loop(self) -> None:
        """The strategy core"""
        logging.info(self.ftx_ws_client.get_ticker('DOGE-PERP'))
        logging.info("Retrieving orders")
        response = self.ftx_rest_api.get("orders", {"market": "DOGE-PERP"})
        logging.info(f"FTX API response: {str(response)}")

    def after_loop(self) -> None:
        time.sleep(2)

    def cleanup(self) -> None:
        """Clean strategy execution"""
        logging.info("BestStratEver cleanup")
