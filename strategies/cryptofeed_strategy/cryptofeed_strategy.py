import logging
import threading
import time
from typing import List

from core.strategy.strategy import Strategy
from strategies.cryptofeed_strategy.cryptofeed_service import CryptofeedService
from strategies.cryptofeed_strategy.enums.cryptofeed_data_type_enum import CryptofeedDataTypeEnum
from strategies.cryptofeed_strategy.enums.cryptofeed_side_enum import CryptofeedSideEnum
from cryptofeed.types import Liquidation

SLEEP_TIME_BETWEEN_LOOPS = 10
LIQUIDATION_HISTORY_RETENTION_TIME = 60 * 60  # 1 hour retention

PAIRS_TO_TRACK = [
    "SOL", "LUNA", "WAVES", "GMT", "AXS", "AVAX", "ZIL", "RUNE", "NEAR", "AAVE", "APE", "ETC", "FIL", "ATOM", "LOOKS",
    "FTM", "ADA", "XRP", "CHZ", "LRC", "DOT", "VET", "GALA", "SUSHI", "FTT", "LINK", "MATIC", "SRM", "SAND", "COMP",
    "EOS", "KNC", "LTC", "ALGO", "SKL", "BCH", "THETA", "SLP", "MANA", "DYDX", "GRT", "FLOW", "ONE", "NEO", "ZEC",
    "PEOPLE", "SNX", "CVC", "ICP", "1INCH", "HBAR", "IMX", "CRO", "AR", "YFI", "RON", "OMG", "REN", "SHIB", "XTZ",
    "ROSE", "CELO", "ANC", "QTUM", "CAKE", "ALPHA", "ICX", "BSV", "TRX", "EGLD", "CHR", "SXP", "RSR", "ENJ", "AUDIO",
    "ENS", "MKR", "XLM", "RAY", "ZRX", "AGLD", "HNT", "ALICE", "PERP", "BAT", "XMR", "KSM", "STMX", "XEM", "MINA",
    "KAVA", "HOT", "DASH", "OKB", "TLM", "STX", "SPELL", "STORJ", "GLMR", "TRU", "DENT", "ATLAS", "DODO", "SCRT", "BAL",
    "ONT", "RNDR", "CVX", "BADGER", "SC", "C98", "IOTA", "MTL", "CLV", "BAND", "TOMO", "ALCX", "PUNDIX", "CREAM",
    "LINA", "MAPS", "TONCOIN", "POLIS", "REEF", "FXS", "STEP", "FIDA", "HUM", "HT", "FLM", "BNT", "AMPL", "PROM",
    "KSOS", "BIT", "BOBA", "DAWN", "RAMP", "YFII", "OXY", "SOS", "LEO", "ORBS", "MTA", "TRYB", "MCB", "EDEN", "MNGO",
    "CONV", "BAO", "SECO", "CEL", "HOLY", "ROOK", "MER", "TULIP", "ASD", "KIN", "MOB", "SRN", "BTT", "MEDIA", "IOST",
    "JASMY", "BTC", "ETH", "DOGE"
]

TIMEFRAMES = [60, 60 * 5]  # 1 min and 5 min
EXCHANGES = ["FTX", "BINANCE_FUTURES"]


class CryptofeedStrategy(Strategy):
    """The test strategy"""

    def __init__(self):
        """The test strategy constructor"""

        logging.info("TestStrategy run strategy")
        super(CryptofeedStrategy, self).__init__()

        # Array liquidation data
        self.liquidations: List[Liquidation] = []

        # {
        #     exchange1: {
        #         coin1: { open_interest: value, timestamp: value },
        #         coin2: { open_interest: value, timestamp: value}
        #     },
        #     ...
        # }
        # Use CryptofeedService EXCHANGES global to configure the list of exchange to retrieve data on
        self.open_interest = {}

        self.computed_liquidations = {}

        # Init computed_liquidations object
        for exchange in EXCHANGES:
            self.computed_liquidations[exchange] = {}
            for timeframe in TIMEFRAMES:
                self.computed_liquidations[exchange][timeframe] = {}

        self._t: threading.Thread = threading.Thread(target=self.strategy_runner)

    def before_loop(self) -> None:
        """Called before each loop"""
        pass

    def loop(self) -> None:
        """The strategy core loop method"""

        self.perform_new_liquidations()
        self.perform_new_open_interest()

        for exchange in EXCHANGES:
            for timeframe in TIMEFRAMES:
                for pair in PAIRS_TO_TRACK:
                    buys = self.get_liquidations(exchanges=[exchange],
                                                 symbols=[pair],
                                                 side=CryptofeedSideEnum.BUY,
                                                 max_age=timeframe)
                    sells = self.get_liquidations(exchanges=[exchange],
                                                  symbols=[pair],
                                                  side=CryptofeedSideEnum.SELL,
                                                  max_age=timeframe)

                    self.computed_liquidations[exchange][timeframe][pair] = {
                        "buy": sum([round(data.quantity * data.price, 2) for data in buys]),
                        "sell": sum([round(data.quantity * data.price, 2) for data in sells])
                    }

        # Put your custom logic here
        # ...

        # Remove values older than LIQUIDATION_HISTORY_RETENTION_TIME
        self.liquidations = list(filter(lambda data: data.timestamp > time.time() - LIQUIDATION_HISTORY_RETENTION_TIME,
                                        self.liquidations))

    def after_loop(self) -> None:
        """Called after each loop"""
        time.sleep(SLEEP_TIME_BETWEEN_LOOPS)

    def cleanup(self) -> None:
        """Clean strategy execution"""
        self._t.join()

    def get_liquidations(self, exchanges: List[str] = None, symbols: List[str] = None, side: CryptofeedSideEnum = None,
                         max_age: int = -1):
        """
        Get the liquidations that meet the given criteria

        :param exchanges: List of exchanges to get liquidations for
        :param symbols: List of symbols to get liquidations for
        :param side: Side to retrieve liquidations for
        :param max_age: Max liquidation age in seconds
        :return: The list of liquidations that meet the criteria
        """

        liquidations = self.liquidations

        if exchanges is not None:
            liquidations = list(filter(lambda data: data.exchange in exchanges, liquidations))

        if symbols is not None:
            liquidations = list(filter(lambda data: any(data.symbol.startswith(sym + "-") for sym in symbols),
                                       liquidations))

        if side is not None:
            liquidations = list(filter(lambda data: data.side == "sell" if side is CryptofeedSideEnum.SELL else "buy",
                                       liquidations))

        if max_age > -1:
            liquidations = list(filter(lambda data: data.timestamp > time.time() - max_age, liquidations))

        return liquidations

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

            self.liquidations.append(data)

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

    def run(self) -> None:
        """
        Override default run method to launch strategy_runner in another thread so cryptofeed can be executed in the
        main thread due to issues when running not in the main thread
        """
        self._t.start()
        CryptofeedService.start_cryptofeed()

    def strategy_runner(self) -> None:
        try:
            while True:
                self.before_loop()
                self.loop()
                self.after_loop()
        except Exception as e:
            logging.info("An error occurred when running strategy")
            logging.info(e)
            self.cleanup()
            raise
