import logging
import time

from core.strategy.strategy import Strategy


class BestStratEver(Strategy):
    """The best strategy ever"""

    def __init__(self):
        """The best strategy ever constructor"""
        super(BestStratEver, self).__init__()

    def startup(self) -> None:
        """Strategy initialisation"""
        logging.info("BestStratEver startup")

    def run_strategy(self) -> None:
        """The strategy core"""
        logging.info("BestStratEver run_strategy")

        while True:
            logging.info(self.ftx_ws_client.get_ticker('DOGE-PERP'))
            time.sleep(2)

    def cleanup(self) -> None:
        """Clean strategy execution"""
        logging.info("BestStratEver cleanup")
