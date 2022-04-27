import logging
import threading
import time
from typing import List

from core.strategy.strategy import Strategy
from strategies.cryptofeed_strategy.cryptofeed_service import CryptofeedService
from strategies.cryptofeed_strategy.enums.cryptofeed_data_type_enum import CryptofeedDataTypeEnum
from strategies.cryptofeed_strategy.models.liquidation_data_dict import LiquidationDataDict
from tools.utils import flatten

SLEEP_TIME_BETWEEN_LOOPS = 10
LIQUIDATION_HISTORY_RETENTION_TIME = 60 * 60  # 1 hour retention


class CryptofeedStrategy(Strategy):
    """The test strategy"""

    def __init__(self):
        """The test strategy constructor"""

        logging.info("TestStrategy run strategy")
        super(CryptofeedStrategy, self).__init__()

        self.liquidations: List[List[LiquidationDataDict]] = []
        self.open_interest = {}
        self._t: threading.Thread = threading.Thread(target=CryptofeedService.start_cryptofeed, args=[])
        self._t.start()

    def before_loop(self) -> None:
        """Called before each loop"""
        pass

    def loop(self) -> None:
        """The strategy core loop method"""

        self.perform_new_liquidations()
        self.perform_new_open_interest()

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

    def perform_new_liquidations(self) -> None:
        """
        Flush new received liquidations from cryptofeed service and add new data to the liquidation array
        """
        new_liquidations = CryptofeedService.flush_liquidation_data_queue_items(CryptofeedDataTypeEnum.LIQUIDATIONS)

        for data in new_liquidations:
            size = round(data.quantity * data.price, 2)

            end_c = '\033[0m'
            side_c = '\033[91m' if data.side == 'sell' else '\33[32m'

            size_c = ''

            if size > 10_000:
                size_c = '\33[32m'
            if size > 25_000:
                size_c = '\33[33m'
            if size > 50_000:
                size_c = '\33[31m'
            if size > 100_000:
                size_c = '\35[35m'

            logging.info(f'{data.exchange:<18} {data.symbol:<18} Side: {side_c}{data.side:<8}{end_c} '
                         f'Quantity: {data.quantity:<10} Price: {data.price:<10} '
                         f'Size: {size_c}{size:<9}{end_c}')  # ID: {data.id} Status: {data.status}')

        self.liquidations.append(new_liquidations)

    def perform_new_open_interest(self) -> None:
        """
        Flush new received open interest from cryptofeed service and add new data to the open interest object
        """

        new_oi = CryptofeedService.flush_liquidation_data_queue_items(CryptofeedDataTypeEnum.OPEN_INTEREST)

        for oi in new_oi:
            if oi.exchange not in self.open_interest:
                self.open_interest[oi.exchange] = {}

            self.open_interest[oi.exchange][oi.symbol] = {
                "open_interest": oi.open_interest,
                "timestamp": oi.timestamp
            }
