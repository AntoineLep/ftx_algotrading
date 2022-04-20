import logging
import time

from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.stock.crypto_pair_manager import CryptoPairManager
from core.strategy.strategy import Strategy


class DemoStrategy(Strategy):
    """The demo strategy"""

    def __init__(self):
        """The demo strategy constructor"""
        logging.info("DemoStrategy run strategy")
        super(DemoStrategy, self).__init__()

        self.ftx_rest_api: FtxRestApi = FtxRestApi()
        self.btc_pair_manager: CryptoPairManager = CryptoPairManager("BTC-PERP", self.ftx_rest_api)
        self.btc_pair_manager.add_time_frame(15)
        self.btc_pair_manager.add_time_frame(60)
        self.btc_pair_manager.start_all_time_frame_acq()

    def before_loop(self) -> None:
        """Called before each loop"""
        logging.info("DemoStrategy before_loop")
        pass

    def loop(self) -> None:
        """The strategy core loop method"""
        logging.info("DemoStrategy loop")
        pass

    def after_loop(self) -> None:
        """Called after each loop"""
        logging.info("DemoStrategy after_loop")
        time.sleep(10)  # Sleep 10 sec

    def cleanup(self) -> None:
        """Clean strategy execution"""
        logging.info("DemoStrategy cleanup")
        self.btc_pair_manager.stop_all_time_frame_acq()
