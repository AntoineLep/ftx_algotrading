import logging
import threading
import time
from typing import List

import pandas as pd
from stockstats import StockDataFrame

from core.enums.order_type_enum import OrderTypeEnum
from core.enums.position_state_enum import PositionStateEnum
from core.enums.side_enum import SideEnum
from core.enums.trigger_order_type_enum import TriggerOrderTypeEnum
from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.models.opening_config_dict import OpeningConfigDict
from core.models.position_config_dict import PositionConfigDict
from core.models.trigger_order_config_dict import TriggerOrderConfigDict
from core.strategy.strategy import Strategy
from core.trading.position_driver import PositionDriver
from strategies.cryptofeed_strategy.cryptofeed_service import CryptofeedService
from strategies.cryptofeed_strategy.enums.cryptofeed_data_type_enum import CryptofeedDataTypeEnum
from strategies.cryptofeed_strategy.enums.cryptofeed_side_enum import CryptofeedSideEnum
from cryptofeed.types import Liquidation

from strategies.cryptofeed_strategy.stock_utils import StockUtils

PAIRS_TO_TRACK = [
    "SOL", "WAVES", "G", "AXS", "AVAX", "ZIL", "RUNE", "NEAR", "AAVE", "APE", "ETC", "FIL", "ATOM", "LOOKS",
    "FTM", "ADA", "XRP", "CHZ", "LRC", "DOT", "VET", "GALA", "SUSHI", "FTT", "LINK", "MATIC", "SRM", "SAND", "COMP",
    "EOS", "KNC", "LTC", "ALGO", "SKL", "BCH", "THETA", "SLP", "MANA", "DYDX", "GRT", "FLOW", "ONE", "NEO", "ZEC",
    "PEOPLE", "SNX", "CVC", "ICP", "1INCH", "HBAR", "IMX", "CRO", "AR", "YFI", "RON", "OMG", "REN", "SHIB", "XTZ",
    "ROSE", "CELO", "ANC", "QTUM", "CAKE", "ALPHA", "ICX", "BSV", "TRX", "EGLD", "CHR", "SXP", "RSR", "ENJ", "AUDIO",
    "ENS", "MKR", "XLM", "RAY", "ZRX", "AGLD", "HNT", "ALICE", "PERP", "BAT", "XMR", "KSM", "STMX", "XEM", "MINA",
    "KAVA", "HOT", "DASH", "OKB", "TLM", "STX", "SPELL", "STORJ", "GLMR", "TRU", "DENT", "ATLAS", "DODO", "SCRT", "BAL",
    "ONT", "RNDR", "CVX", "BADGER", "SC", "C98", "IOTA", "MTL", "CLV", "BAND", "TOMO", "ALCX", "PUNDIX", "CREAM",
    "LINA", "MAPS", "TONCOIN", "POLIS", "REEF", "FXS", "STEP", "FIDA", "HT", "FLM", "BNT", "AMPL", "PROM",
    "KSOS", "BIT", "BOBA", "DAWN", "YFII", "OXY", "SOS", "LEO", "TRYB", "EDEN", "MNGO", "SECO", "CEL", "HOLY", "ASD",
    "MOB", "BTT", "MEDIA", "IOST", "JASMY", "BTC", "ETH", "DOGE"
]

SLEEP_TIME_BETWEEN_LOOPS = 10
LIQUIDATION_HISTORY_RETENTION_TIME = 60 * 60  # 1 hour retention
TAKE_PROFIT_PERCENTAGE_1 = 1
TIMEFRAMES = [60]  # 1 min
EXCHANGES = ["FTX", "BINANCE_FUTURES"]
TRIGGER_LIQUIDATION_VALUE = 10000
LIQUIDATIONS_OI_RATIO_THRESHOLD = 500
MAX_SIMULTANEOUSLY_OPENED_POSITIONS = 5
STOP_LOSS_ATR = 1
RISK_PER_TRADE = 0.05
TAKE_PROFIT_ATR = 3


class CryptofeedStrategy(Strategy):
    """The test strategy"""

    def __init__(self):
        """The test strategy constructor"""

        logging.info("TestStrategy run strategy")
        super(CryptofeedStrategy, self).__init__()

        self.ftx_rest_api: FtxRestApi = FtxRestApi()

        # Array liquidation data
        self.liquidations: List[Liquidation] = []

        # Dict [pair] -> PositionDriver
        self.positions = {}

        # {
        #     exchange1: {
        #         coin1: { open_interest: value, timestamp: value },
        #         coin2: { open_interest: value, timestamp: value}
        #     },
        #     ...
        # }
        # Use CryptofeedService EXCHANGES global to configure the list of exchange to retrieve data on
        self.open_interest = {}

        for exchange in EXCHANGES:
            self.open_interest[exchange] = {}

        self.computed_liquidations = {}

        # Init computed_liquidations object
        for exchange in EXCHANGES:
            self.computed_liquidations[exchange] = {}
            for timeframe in TIMEFRAMES:
                self.computed_liquidations[exchange][timeframe] = {}

        self.timeframes_close_ts = {}
        for timeframe in TIMEFRAMES:
            self.timeframes_close_ts[timeframe] = time.time() + timeframe

        # Dict of running position drivers
        self.position_drivers = {}

        StockDataFrame.BOLL_STD_TIMES = 4

        self._t: threading.Thread = threading.Thread(target=self.strategy_runner)

    def before_loop(self) -> None:
        """Called before each loop"""
        pass

    def loop(self) -> None:
        """The strategy core loop method"""

        self.perform_new_liquidations()
        self.perform_new_open_interest()
        self.perform_liquidations()

        for timeframe in TIMEFRAMES:
            # Liquidation candle close
            if time.time() > self.timeframes_close_ts[timeframe]:
                # Set next timeframe end timestamp
                self.timeframes_close_ts[timeframe] = time.time() + timeframe
                self.perform_data_analysis(timeframe)

        # Remove values older than LIQUIDATION_HISTORY_RETENTION_TIME
        self.liquidations = list(filter(lambda data: data.timestamp > time.time() - LIQUIDATION_HISTORY_RETENTION_TIME,
                                        self.liquidations))

    def after_loop(self) -> None:
        """Called after each loop"""
        time.sleep(SLEEP_TIME_BETWEEN_LOOPS)

    def cleanup(self) -> None:
        """Clean strategy execution"""
        self._t.join()

    def perform_data_analysis(self, timeframe: int):
        for pair in PAIRS_TO_TRACK:
            try:
                buy_liquidation_sum = sum(
                    [self.computed_liquidations[exchange][timeframe][pair]['buy'] for exchange in EXCHANGES])
                sell_liquidation_sum = sum(
                    [self.computed_liquidations[exchange][timeframe][pair]['sell'] for exchange in EXCHANGES])

                if buy_liquidation_sum > 1000 or sell_liquidation_sum > 1000:
                    logging.info(f"Liquidations for pair: {pair:<10} - buy: ${buy_liquidation_sum:<12} - "
                                 f"sell: ${sell_liquidation_sum:<12}")

                    # Check we got oi data for all listed exchanges
                    if all([pair in self.open_interest[exchange] for exchange in EXCHANGES]):

                        # Check the liquidations (buy or sell) exceeds the TRIGGER_LIQUIDATION_VALUE
                        if buy_liquidation_sum > TRIGGER_LIQUIDATION_VALUE or \
                                sell_liquidation_sum > TRIGGER_LIQUIDATION_VALUE:

                            # Getting current price of pair
                            current_price = StockUtils.get_market_price(self.ftx_rest_api, pair + '-PERP')

                            # Sum the open interest usd value for listed exchanges
                            oi_sum_usd = 0
                            for exchange in EXCHANGES:
                                cur_exchange_oi_usd = round(
                                    float(self.open_interest[exchange][pair]["open_interest"]) * current_price, 1)
                                oi_sum_usd += cur_exchange_oi_usd
                                logging.info(f'oi_sum_usd for {exchange} {pair} - ${cur_exchange_oi_usd:_}')

                            logging.info(f'oi_sum_usd for {pair} - ${oi_sum_usd:_}')

                            # Open position logic
                            if buy_liquidation_sum * LIQUIDATIONS_OI_RATIO_THRESHOLD > oi_sum_usd:
                                self.open_position(pair, SideEnum.SELL)
                            elif sell_liquidation_sum * LIQUIDATIONS_OI_RATIO_THRESHOLD > oi_sum_usd:
                                self.open_position(pair, SideEnum.BUY)
            except Exception as e:
                logging.error(e)
                pass

    @staticmethod
    def compute_quantity(current_price: float, atr_14: pd.DataFrame, available_balance_without_borrow: float,
                         side: SideEnum) -> float:
        stop = current_price - (atr_14.iloc[-1] * STOP_LOSS_ATR if side == SideEnum.BUY else
                                atr_14.iloc[-1] * TAKE_PROFIT_ATR)
        trade_risk = available_balance_without_borrow * RISK_PER_TRADE
        entry_stop = current_price - stop
        qty = trade_risk / entry_stop
        return qty

    def open_position(self, pair: str, side: SideEnum) -> None:
        # Don't reopen a position if there is a position driver already opened
        if pair in self.position_drivers and self.position_drivers[pair].position_state == PositionStateEnum.OPENED:
            return

        opened_position_number = sum(1 if self.position_drivers[key] and
                                     self.position_drivers[key].position_state == PositionStateEnum.OPENED
                                     else 0 for key in self.position_drivers)

        if opened_position_number >= MAX_SIMULTANEOUSLY_OPENED_POSITIONS:
            return

        stockstats_candles = StockUtils.get_last_x_stockstats_candles(self.ftx_rest_api, pair, 20)
        atr_14 = StockUtils.get_atr_14(stockstats_candles)
        logging.info(f"{pair} - atr_14: {atr_14.iloc[-1]}")

        # Getting current price of pair
        current_price = StockUtils.get_market_price(self.ftx_rest_api, pair + '-PERP')

        available_balance_without_borrow = StockUtils.get_available_balance_without_borrow(self.ftx_rest_api,)
        logging.info(f'available without borrow: ${available_balance_without_borrow}')
        quantity = CryptofeedStrategy.compute_quantity(current_price, atr_14, available_balance_without_borrow, side)

        openings: List[OpeningConfigDict] = [{
            "price": None,
            "size": quantity,
            "type": OrderTypeEnum.MARKET
        }]
        sl: TriggerOrderConfigDict = {
            "size": quantity,
            "type": TriggerOrderTypeEnum.STOP,
            "reduce_only": True,
            "trigger_price": current_price - (atr_14.iloc[-1] * STOP_LOSS_ATR) if side == SideEnum.BUY
            else current_price + atr_14.iloc[-1],
            "order_price": None,
            "trail_value": None
        }
        tp1: TriggerOrderConfigDict = {
            "size": quantity,
            "type": TriggerOrderTypeEnum.TAKE_PROFIT,
            "reduce_only": True,
            "trigger_price": current_price + (atr_14.iloc[-1] * TAKE_PROFIT_ATR) if side == SideEnum.BUY
            else current_price - (atr_14.iloc[-1] * TAKE_PROFIT_ATR),
            "order_price": None,
            "trail_value": None
        }
        position_config: PositionConfigDict = {
            "openings": openings,
            "trigger_orders": [sl, tp1],
            "max_open_duration": 60 * 60 * 24
        }

        self.position_drivers[pair] = PositionDriver(self.ftx_rest_api, 60)
        self.position_drivers[pair].open_position(pair + '-PERP', side, position_config)

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
            liquidations = list(
                filter(lambda data: data.side == "sell" if side is CryptofeedSideEnum.SELL else data.side == "buy",
                       liquidations)
            )

        if max_age > -1:
            liquidations = list(filter(lambda data: data.timestamp > time.time() - max_age, liquidations))

        return liquidations

    def perform_liquidations(self) -> None:
        """
        Compute a sum of all liquidations into the configured timeframes for listed exchanges
        """
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
            symbol = next(filter(lambda sym: oi.symbol.startswith(sym + "-"), PAIRS_TO_TRACK), None)

            # If the open interest data already exists
            if symbol in self.open_interest[oi.exchange]:

                # Check the new open interest value is not more than 3 times less than the last received value to
                # prevent cryptofeed wrong data (eg. not perp future) from getting performed
                if oi.open_interest * 3 > self.open_interest[oi.exchange][symbol]["open_interest"]:
                    self.open_interest[oi.exchange][symbol] = {
                        "open_interest": oi.open_interest,
                        "timestamp": oi.timestamp
                    }
            else:
                self.open_interest[oi.exchange][symbol] = {
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
