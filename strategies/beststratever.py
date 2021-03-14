import copy
import logging
import time

from core.strategy.strategy import Strategy


class BestStratEver(Strategy):
    """The best strategy ever"""

    def __init__(self):
        """The best strategy ever constructor"""
        super(BestStratEver, self).__init__()

    def startup(self):
        """Strategy initialisation"""
        logging.info("BestStratEver startup")

    def run_strategy(self):
        """The strategy core"""
        logging.info("BestStratEver run_strategy")

        while True:
            time.sleep(5)

    def cleanup(self):
        """Clean strategy execution"""
        logging.info("BestStratEver cleanup")
