import asyncio
import logging
import queue

from cryptofeed import FeedHandler
from cryptofeed.defines import LIQUIDATIONS
from cryptofeed.exchanges import EXCHANGE_MAP

# Display all received data if set to true. Only the data > min_data_size is displayed otherwise
DISPLAY_ALL_LIQUIDATION_DATA = True


class CryptofeedService(object):
    LIQUIDATION_DATA: queue.Queue = queue.Queue()

    @staticmethod
    def flush_liquidation_data_queue_items(min_data_size: int = 0):
        """
        Flush TestStrategy.LIQUIDATION_DATA queue and returns the data having a value >= min_data_size

        :return: The data having a size >= min_data_size
        """
        items = []

        while not CryptofeedService.LIQUIDATION_DATA.empty():
            data = CryptofeedService.LIQUIDATION_DATA.get()

            if DISPLAY_ALL_LIQUIDATION_DATA:
                logging.info(data)

            size = round(data.quantity * data.price, 2)

            if size >= min_data_size:
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

                items.append(data)

        return items

    @staticmethod
    def start_cryptofeed():
        async def liquidations(data, receipt):
            # Add raw data to TestStrategy.LIQUIDATION_DATA queue
            CryptofeedService.LIQUIDATION_DATA.put(data)

        # There is no current event loop in thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        f = FeedHandler()
        configured = []

        # ['BINANCE_DELIVERY', 'BINANCE_FUTURES', 'BITMEX', 'BYBIT', 'DERIBIT', 'FTX']
        exchanges = ['BINANCE_FUTURES', 'FTX']

        # print(type(EXCHANGE_MAP), EXCHANGE_MAP)
        print("Querying exchange metadata")
        for exchange_string, exchange_class in EXCHANGE_MAP.items():

            if exchange_string not in exchanges:
                continue

            if exchange_string in ['BITFLYER', 'EXX', 'OKEX']:  # We have issues with these exchanges
                continue

            if LIQUIDATIONS in exchange_class.info()['channels']['websocket']:
                configured.append(exchange_string)
                print(f"Configuring {exchange_string}...", end='')
                symbols = [sym for sym in exchange_class.symbols() if 'PINDEX' not in sym]
                # symbols = ['LRC-USDT-PERP']
                # print(symbols)
                try:
                    f.add_feed(exchange_class(subscription={LIQUIDATIONS: symbols},
                                              callbacks={LIQUIDATIONS: liquidations}))
                    print(" Done")
                except Exception as e:
                    print(e, exchange_string)
                    pass

        print(configured)

        print("Starting feedhandler for exchanges:", ', '.join(configured))
        f.run(install_signal_handlers=False)
