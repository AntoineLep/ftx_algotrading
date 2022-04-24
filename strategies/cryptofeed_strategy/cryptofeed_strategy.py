import logging
import threading
import time

from core.strategy.strategy import Strategy
from strategies.cryptofeed_strategy.cryptofeed_service import CryptofeedService
from tools.utils import flatten

SLEEP_TIME_BETWEEN_LOOPS = 10
LIQUIDATION_HISTORY_RETENTION_TIME = 60 * 60  # 1 hour retention


class CryptofeedStrategy(Strategy):
    """The test strategy"""

    def __init__(self):
        """The test strategy constructor"""

        logging.info("TestStrategy run strategy")
        super(CryptofeedStrategy, self).__init__()

        self.liquidations = []
        self._t: threading.Thread = threading.Thread(target=CryptofeedService.start_cryptofeed)
        self._t.start()

    def before_loop(self) -> None:
        """Called before each loop"""
        pass

    def loop(self) -> None:
        """The strategy core loop method"""

        # Flush liquidation data received into TestStrategy.LIQUIDATION_DATA queue
        # Put in parameters the minimum value of the liquidation you want to retrieve
        new_liquidations = CryptofeedService.flush_liquidation_data_queue_items(0)

        self.liquidations.append(new_liquidations)

        last_1_min_liquidations = flatten(
            self.liquidations[-min(len(self.liquidations), 60 // SLEEP_TIME_BETWEEN_LOOPS):])
        last_5_min_liquidations = flatten(
            self.liquidations[-min(len(self.liquidations), 60 * 5 // SLEEP_TIME_BETWEEN_LOOPS):])

        last_1_min_liquidations_value = sum([round(data.quantity * data.price, 2) for data in last_1_min_liquidations])
        last_5_min_liquidations_value = sum([round(data.quantity * data.price, 2) for data in last_5_min_liquidations])

        logging.info(f'Liquidations in the last 1 minute: {len(last_1_min_liquidations)} for a total value of '
                     f'${last_1_min_liquidations_value}')
        logging.info(f'Liquidations in the last 5 minutes: {len(last_5_min_liquidations)} for a total value of '
                     f'${last_5_min_liquidations_value}')

        # Put your custom logic here
        # ...

        # Remove values older than LIQUIDATION_HISTORY_RETENTION_TIME
        if len(self.liquidations) > LIQUIDATION_HISTORY_RETENTION_TIME // SLEEP_TIME_BETWEEN_LOOPS:
            self.liquidations = self.liquidations[-LIQUIDATION_HISTORY_RETENTION_TIME // SLEEP_TIME_BETWEEN_LOOPS:]

    def after_loop(self) -> None:
        """Called after each loop"""
        time.sleep(SLEEP_TIME_BETWEEN_LOOPS)

    def cleanup(self) -> None:
        """Clean strategy execution"""
        self._t.join()
