import logging
import queue
from typing import List

from cryptofeed import FeedHandler
from cryptofeed.defines import LIQUIDATIONS, OPEN_INTEREST
from cryptofeed.exchanges import EXCHANGE_MAP

from strategies.cryptofeed_strategy.enums.cryptofeed_data_type_enum import CryptofeedDataTypeEnum

# Display all received data if set to true (verbose)
DISPLAY_ALL_DATA = False
EXCHANGES = ['BINANCE_FUTURES', 'FTX']


class CryptofeedService(object):
    data = {
        CryptofeedDataTypeEnum.LIQUIDATIONS: queue.Queue(),
        CryptofeedDataTypeEnum.OPEN_INTEREST: queue.Queue()
    }

    @staticmethod
    def flush_liquidation_data_queue_items(data_type: CryptofeedDataTypeEnum) -> List:
        """
        Flush TestStrategy.LIQUIDATION_DATA queue and returns the data

        :param data_type: The type of data to flush
        :return: The liquidation data
        """
        items = []

        while not CryptofeedService.data[data_type].empty():
            data = CryptofeedService.data[data_type].get()

            if DISPLAY_ALL_DATA:
                logging.info(data)

            items.append(data)

        return items

    @staticmethod
    def start_cryptofeed():
        async def liquidations_cb(data, receipt):
            # Add raw data to CryptofeedDataTypeEnum.LIQUIDATION_DATA queue
            CryptofeedService.data[CryptofeedDataTypeEnum.LIQUIDATIONS].put(data)

        async def open_interest_cb(data, receipt):
            # Add raw data to CryptofeedDataTypeEnum.OPEN_INTEREST queue
            CryptofeedService.data[CryptofeedDataTypeEnum.OPEN_INTEREST].put(data)

        while True:
            try:
                f = FeedHandler()
                configured = []

                print("Querying exchange metadata")
                for exchange_string, exchange_class in EXCHANGE_MAP.items():

                    if exchange_string not in EXCHANGES:
                        continue

                    if exchange_string in ['BITFLYER', 'EXX', 'OKEX']:  # We have issues with these exchanges
                        continue

                    if all(channel in exchange_class.info()['channels']['websocket'] for channel in [LIQUIDATIONS,
                                                                                                     OPEN_INTEREST]):
                        configured.append(exchange_string)
                        print(f"Configuring {exchange_string}...", end='')
                        symbols = [sym for sym in exchange_class.symbols() if 'PINDEX' not in sym and 'LUNA' not in sym]

                        try:
                            f.add_feed(exchange_class(subscription={LIQUIDATIONS: symbols, OPEN_INTEREST: symbols},
                                                      callbacks={LIQUIDATIONS: liquidations_cb,
                                                                 OPEN_INTEREST: open_interest_cb}))
                            print(" Done")
                        except Exception as e:
                            print(e, exchange_string)
                            pass

                print(configured)

                print("Starting feedhandler for exchanges:", ', '.join(configured))
                f.run(install_signal_handlers=False)
            except KeyboardInterrupt:  # pragma: no cover
                raise
            except Exception as e:
                logging.error(e)
                pass
