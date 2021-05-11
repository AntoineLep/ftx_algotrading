import logging
import time

from core.strategy.strategy import Strategy
from core.ftx.ws.ftx_websocket_client import FtxWebsocketClient


class BestStrategyEver(Strategy):
    """The best strategy ever"""

    def __init__(self):
        """The best strategy ever constructor"""

        logging.info("BestStrategyEver run strategy")
        super(BestStrategyEver, self).__init__()

        self.ftx_ws_client: FtxWebsocketClient = FtxWebsocketClient()
        self.ftx_ws_client.connect()

    def before_loop(self) -> None:
        pass

    def loop(self) -> None:
        """The strategy core"""
        logging.info(self.ftx_ws_client.get_ticker('DOGE-PERP'))

    def after_loop(self) -> None:
        time.sleep(2)

    def cleanup(self) -> None:
        """Clean strategy execution"""
        logging.info("BestStratEver cleanup")
