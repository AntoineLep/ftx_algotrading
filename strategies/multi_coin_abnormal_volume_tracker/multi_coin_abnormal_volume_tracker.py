import logging
import math
import time

from core.enums.color_enum import ColorEnum
from core.enums.order_type_enum import OrderTypeEnum
from core.enums.position_state_enum import PositionStateEnum
from core.enums.side_enum import SideEnum
from core.enums.trigger_order_type_enum import TriggerOrderTypeEnum
from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.models.market_data_dict import MarketDataDict
from core.models.position_config_dict import PositionConfigDict
from core.models.trigger_order_config_dict import TriggerOrderConfigDict
from core.models.wallet_dict import WalletDict
from core.stock.crypto_pair_manager import CryptoPairManager
from core.stock.time_frame_manager import TimeFrameManager
from core.strategy.strategy import Strategy
from core.trading.position_driver import PositionDriver
from strategies.multi_coin_abnormal_volume_tracker.models.pair_manager_dict import PairManagerDict
from tools.utils import format_wallet_raw_data, format_market_raw_data

PAIRS_TO_TRACK = [
    "SOL-PERP", "WAVES-PERP", "GMT-PERP", "AXS-PERP", "AVAX-PERP", "ZIL-PERP",
    "RUNE-PERP", "NEAR-PERP", "AAVE-PERP", "APE-PERP", "ETC-PERP", "FIL-PERP", "ATOM-PERP", "LOOKS-PERP", "FTM-PERP",
    "ADA-PERP", "XRP-PERP", "CHZ-PERP", "LRC-PERP", "DOT-PERP", "VET-PERP", "GALA-PERP", "SUSHI-PERP", "FTT-PERP",
    "LINK-PERP", "MATIC-PERP", "SRM-PERP", "SAND-PERP", "COMP-PERP", "EOS-PERP", "KNC-PERP", "LTC-PERP",
    "ALGO-PERP", "SKL-PERP", "BCH-PERP", "THETA-PERP", "SLP-PERP", "MANA-PERP", "DYDX-PERP", "GRT-PERP", "FLOW-PERP",
    "ONE-PERP", "NEO-PERP", "ZEC-PERP", "PEOPLE-PERP", "SNX-PERP", "CVC-PERP", "ICP-PERP", "1INCH-PERP", "HBAR-PERP",
    "IMX-PERP", "CRO-PERP", "AR-PERP", "YFI-PERP", "RON-PERP", "OMG-PERP", "REN-PERP", "SHIB-PERP", "XTZ-PERP",
    "ROSE-PERP", "CELO-PERP", "ANC-PERP", "QTUM-PERP", "CAKE-PERP", "ALPHA-PERP", "ICX-PERP", "BSV-PERP", "TRX-PERP",
    "EGLD-PERP", "CHR-PERP", "SXP-PERP", "RSR-PERP", "ENJ-PERP", "AUDIO-PERP", "ENS-PERP", "MKR-PERP", "XLM-PERP",
    "RAY-PERP", "ZRX-PERP", "AGLD-PERP", "HNT-PERP", "ALICE-PERP", "PERP-PERP", "BAT-PERP", "XMR-PERP", "KSM-PERP",
    "STMX-PERP", "XEM-PERP", "MINA-PERP", "KAVA-PERP", "HOT-PERP", "DASH-PERP", "OKB-PERP", "TLM-PERP", "STX-PERP",
    "SPELL-PERP", "STORJ-PERP", "GLMR-PERP", "TRU-PERP", "DENT-PERP", "ATLAS-PERP", "DODO-PERP", "SCRT-PERP",
    "BAL-PERP", "ONT-PERP", "RNDR-PERP", "CVX-PERP", "BADGER-PERP", "SC-PERP", "C98-PERP", "IOTA-PERP", "MTL-PERP",
    "CLV-PERP", "BAND-PERP", "TOMO-PERP", "ALCX-PERP", "PUNDIX-PERP", "CREAM-PERP", "LINA-PERP", "MAPS-PERP",
    "TONCOIN-PERP", "POLIS-PERP", "REEF-PERP", "FXS-PERP", "STEP-PERP", "FIDA-PERP", "HT-PERP", "FLM-PERP",
    "BNT-PERP", "AMPL-PERP", "PROM-PERP", "KSOS-PERP", "BIT-PERP", "BOBA-PERP", "DAWN-PERP", "YFII-PERP", "OXY-PERP",
    "SOS-PERP", "LEO-PERP", "TRYB-PERP", "EDEN-PERP", "MNGO-PERP", "SECO-PERP", "CEL-PERP", "HOLY-PERP", "ASD-PERP",
    "MOB-PERP", "BTT-PERP", "MEDIA-PERP", "IOST-PERP", "JASMY-PERP", "GAL-PERP", "GST-PERP"
]

# FTX api rate limit is 10 requests per second
TIME_TO_SLEEP_BETWEEN_TIMEFRAME_LAUNCH = 0.25  # Sleeping 250 ms will avoid errors with a reasonable tolerance

LONG_MA_VOLUME_DEPTH = 100  # The number of candles to be used as volume comparison base
SHORT_MA_VOLUME_DEPTH = 4  # The number of candles used to compare volume on (must be < than LONG_MA_VOLUME_DEPTH)

# There must be this ratio of green candle on the last SHORT_MA_VOLUME_DEPTH candles
SHORT_MA_GREEN_CANDLE_DOMINANCE_MIN_RATIO = 0.75

# Factor by which the SHORT_MA_VOLUME_DEPTH volume must be higher than LONG_MA_VOLUME_DEPTH volume
VOLUME_CHECK_FACTOR_SIZE = 15

MINIMUM_AVERAGE_VOLUME = 15000  # Minimum average volume to pass validation (avoid unsellable coin)
MINIMUM_PRICE_VARIATION = 0.6  # Percentage of variation a coin must have during its last SHORT_MA_VOLUME_DEPTH candles
POSITION_LEVERAGE = 0.2  # Position leverage to apply on each position
TRAILING_STOP_PERCENTAGE = 2.2  # Trailing stop percentage
STOP_LOSS_PERCENTAGE = 0.6  # Stop loss percentage

POSITION_DRIVER_WORKER_SLEEP_TIME_BETWEEN_LOOPS = 120  # When a position driver is running, check market every x sec
POSITION_MAX_OPEN_DURATION = 4 * 60 * 60
JAIL_DURATION = 60 * 60  # Time for wish a coin can't be re bought after a position is closed on it


class MultiCoinAbnormalVolumeTracker(Strategy):
    """Multi coin abnormal volume tracker"""

    def __init__(self):
        """The multi coin abnormal volume tracker strategy constructor"""

        logging.info("MultiCoinAbnormalVolumeTracker run strategy")
        super(MultiCoinAbnormalVolumeTracker, self).__init__()

        # Deactivate stock data log for readability purposes
        TimeFrameManager.log_received_stock_data = False

        self.ftx_rest_api: FtxRestApi = FtxRestApi()
        self.pair_manager_list = {}  # { [pair]: pair_manager }

        self.total_invested = 0

        # Compute all market volume during the last SHORT_MA_VOLUME_DEPTH candles to apply a coefficient on
        # VOLUME_CHECK_FACTOR_SIZE accordingly (the more the market is volume is pumping, the more it will be difficult
        # to trigger VOLUME_CHECK_FACTOR_SIZE check
        self.current_market_volume_indicator = 1

        i = 0
        for pair_to_track in PAIRS_TO_TRACK:
            i += 1
            print(f"Initializing pair {i} of {len(PAIRS_TO_TRACK)}: {pair_to_track}")
            crypto_pair_manager = CryptoPairManager(pair_to_track, self.ftx_rest_api)
            crypto_pair_manager.add_time_frame(60, False)
            crypto_pair_manager.start_all_time_frame_acq()

            pair_manager: PairManagerDict = {
                "crypto_pair_manager": crypto_pair_manager,
                "position_driver": None,
                "last_position_driver_state": PositionStateEnum.NOT_OPENED,
                "jail_start_timestamp": 0,
                "invested": 0
            }

            self.pair_manager_list[pair_to_track] = pair_manager
            time.sleep(TIME_TO_SLEEP_BETWEEN_TIMEFRAME_LAUNCH)

    def before_loop(self) -> None:
        pass

    def loop(self) -> None:
        """The strategy core"""

        logging.info("Compute overall market volume indicator ...")

        # This indicator will help to not trigger too many coin position openings when the whole market is pumping
        self.compute_all_market_volume_indicator()
        logging.info(f"Overall market volume indicator = {self.current_market_volume_indicator}")

        logging.info("Scanning markets ...")

        # For each coin
        for pair_to_track in PAIRS_TO_TRACK:
            try:
                pair_manager: PairManagerDict = self.pair_manager_list[pair_to_track]

                if self.decide(pair_to_track):
                    logging.info(f"Market:{pair_to_track}, all decision checks passed ! Let's buy this :)")

                    if self.open_position(pair_to_track):
                        pair_manager["last_position_driver_state"] = PositionStateEnum.OPENED
                    else:
                        logging.info(f"Market:{pair_to_track}, position driver attempt to open position failed.")
            except Exception as e:
                logging.error(e)
                continue  # Loop over the next coin
        logging.info("Markets scanned !")

    def after_loop(self) -> None:
        time.sleep(10)

    def cleanup(self) -> None:
        """Clean strategy execution"""
        logging.info("MultiCoinAbnormalVolumeTracker cleanup")

        i = 0
        for pair_to_track in PAIRS_TO_TRACK:
            i += 1
            logging.info(f"Stopping time frame acquisition on pair {i} of {len(PAIRS_TO_TRACK)}: {pair_to_track}")
            self.pair_manager_list[pair_to_track]["crypto_pair_manager"].stop_all_time_frame_acq()

    def compute_all_market_volume_indicator(self):
        """
        Compute an indicator of how much the short ma on every coin volume is more (indicator > 1)
        or less (indicator < 1) than the long ma volume
        """
        all_pairs_volume_factor_sum = 0
        all_pairs_number = 0

        # For each coin
        for pair_to_track in PAIRS_TO_TRACK:
            pair_manager: PairManagerDict = self.pair_manager_list[pair_to_track]
            stock_data_manager = pair_manager["crypto_pair_manager"].get_time_frame(60).stock_data_manager

            # Not enough data
            if len(stock_data_manager.stock_data_list) < LONG_MA_VOLUME_DEPTH + SHORT_MA_VOLUME_DEPTH:
                continue

            lma_sum_volume = sum([d.volume for d in stock_data_manager.stock_data_list[
                                                    -(LONG_MA_VOLUME_DEPTH + SHORT_MA_VOLUME_DEPTH):
                                                    -SHORT_MA_VOLUME_DEPTH]])
            lma_avg_volume = lma_sum_volume / LONG_MA_VOLUME_DEPTH

            sma_sum_volume = sum([d.volume for d in stock_data_manager.stock_data_list[-SHORT_MA_VOLUME_DEPTH:]])
            sma_avg_volume = sma_sum_volume / SHORT_MA_VOLUME_DEPTH

            # Don't consider coins without sma avg volume as well
            if lma_avg_volume > 0 and sma_avg_volume > 0:
                all_pairs_number += 1
                # Avoid having too high or too low volume factor values by capping the factor between 0.5 and 4
                if sma_avg_volume / lma_avg_volume < 0.5:
                    all_pairs_volume_factor_sum += 0.5
                elif sma_avg_volume / lma_avg_volume > 4:
                    all_pairs_volume_factor_sum += 4
                else:
                    all_pairs_volume_factor_sum += sma_avg_volume / lma_avg_volume

        self.current_market_volume_indicator = round(all_pairs_volume_factor_sum / all_pairs_number, 2) \
            if all_pairs_number != 0 else 1

    def decide(self, pair: str) -> bool:
        """
        Decide to open or not a position on a given pair

        :param pair: The pair to open a position on
        :return: True if the position is successfully opened, False otherwise
        """

        pair_manager: PairManagerDict = self.pair_manager_list[pair]

        # Check the coin is not currently bought (position driver running)
        if pair_manager["position_driver"] is not None \
                and pair_manager["position_driver"].position_state is PositionStateEnum.OPENED:
            return False  # Skip this coin

        # First time we loop after a position was closed
        if pair_manager["last_position_driver_state"] == PositionStateEnum.OPENED:
            self.total_invested = self.total_invested - pair_manager["invested"]
            pair_manager["last_position_driver_state"] = PositionStateEnum.NOT_OPENED
            pair_manager["jail_start_timestamp"] = int(time.time())

        # Coin is in jail after a position was closed
        if int(time.time()) < pair_manager["jail_start_timestamp"] + JAIL_DURATION:
            return False  # Skip this coin

        stock_data_manager = pair_manager["crypto_pair_manager"].get_time_frame(60).stock_data_manager

        # Not enough data
        if len(stock_data_manager.stock_data_list) < LONG_MA_VOLUME_DEPTH + SHORT_MA_VOLUME_DEPTH:
            return False

        # Compute zero volume candles number
        zero_volume_candles_number = sum(map(
            lambda x: x == 0,
            [d.volume for d in stock_data_manager.stock_data_list[-(LONG_MA_VOLUME_DEPTH + SHORT_MA_VOLUME_DEPTH):
                                                                  -SHORT_MA_VOLUME_DEPTH]]
        ))

        # Too many zero volume candles
        if zero_volume_candles_number > LONG_MA_VOLUME_DEPTH / 3:
            return False  # Skip this coin

        # Check average LONG_MA_VOLUME_DEPTH (lma) candles volume is VOLUME_CHECK_FACTOR_SIZE times more
        # than the average SHORT_MA_VOLUME_DEPTH (sma)
        lma_sum_volume = sum([d.volume for d in stock_data_manager.stock_data_list[
                                                -(LONG_MA_VOLUME_DEPTH + SHORT_MA_VOLUME_DEPTH):
                                                -SHORT_MA_VOLUME_DEPTH]])

        # Don't consider zero volume candles
        lma_avg_volume = lma_sum_volume / (LONG_MA_VOLUME_DEPTH - zero_volume_candles_number)

        sma_sum_volume = sum([d.volume for d in stock_data_manager.stock_data_list[-SHORT_MA_VOLUME_DEPTH:]])
        sma_avg_volume = sma_sum_volume / SHORT_MA_VOLUME_DEPTH

        # Increase VOLUME_CHECK_FACTOR_SIZE applied value using current_market_indicator (if indicator is more than 1)
        applied_volume_factor = max(VOLUME_CHECK_FACTOR_SIZE,
                                    VOLUME_CHECK_FACTOR_SIZE * self.current_market_volume_indicator)

        # If recent volume are not applied_volume_factor time more than older volume
        if sma_avg_volume == 0 or sma_avg_volume / lma_avg_volume < applied_volume_factor:
            # log volumes that are higher than 1/3 the required volumes
            if lma_avg_volume != 0 and sma_avg_volume / lma_avg_volume > math.floor(applied_volume_factor / 3):
                logging.info(f"Market:{pair}, volume factor check: "
                             f"{sma_avg_volume} / {lma_avg_volume} = {sma_avg_volume / lma_avg_volume}")
            return False  # Skip this coin

        logging.info(f"Market:{pair}, volume factor check passes ! "
                     f"{sma_avg_volume} > {lma_avg_volume} * {applied_volume_factor}")

        green_candles_number = 0

        # Individual candle checks
        for i in range(1, SHORT_MA_VOLUME_DEPTH + 1):

            # Count green candles
            if stock_data_manager.stock_data_list[-i].get_color() is ColorEnum.GREEN:
                green_candles_number += 1

            # Volume factor check
            if stock_data_manager.stock_data_list[-i].volume / lma_avg_volume < applied_volume_factor:
                logging.info(f"Market:{pair}, volume individual candle check fail !")
                return False  # Skip this coin

            # Volume minimum value check
            if stock_data_manager.stock_data_list[-i].volume < MINIMUM_AVERAGE_VOLUME:
                logging.info(f"Market:{pair}, volume minimum value check fail ! "
                             f"{stock_data_manager.stock_data_list[-i].volume} < {MINIMUM_AVERAGE_VOLUME}")
                return False  # Skip this coin

        if green_candles_number / SHORT_MA_VOLUME_DEPTH < SHORT_MA_GREEN_CANDLE_DOMINANCE_MIN_RATIO:
            logging.info(f"Market:{pair}, green candle dominance check fail ! "
                         f"{green_candles_number} green candle(s) is less than {SHORT_MA_VOLUME_DEPTH} * "
                         f"{SHORT_MA_GREEN_CANDLE_DOMINANCE_MIN_RATIO}")
            return False  # Skip this coin

        logging.info(f"Market:{pair}, Volume check passes ! "
                     f"{sma_avg_volume} >= {MINIMUM_AVERAGE_VOLUME}")

        # Check the price is up from at least MINIMUM_PRICE_VARIATION %
        candle_before = stock_data_manager.stock_data_list[-(SHORT_MA_VOLUME_DEPTH + 1)]
        last_candle = stock_data_manager.stock_data_list[-1]

        if last_candle.close_price < candle_before.open_price * (1 + MINIMUM_PRICE_VARIATION / 100):
            logging.info(f"Market:{pair}, price minimum check fail ! "
                         f"{last_candle.close_price} < "
                         f"{candle_before.open_price * (1 + MINIMUM_PRICE_VARIATION / 100)}")
            return False  # Skip this coin

        logging.info(f"Market:{pair}, price minimum check passes ! "
                     f"{last_candle.close_price} >= {candle_before.open_price} * {MINIMUM_PRICE_VARIATION}%")

        return True

    def open_position(self, pair: str) -> bool:
        """
        Compute position price, setup stop loss and open position

        :param pair: The pair to open a position on
        :return: True if the position is successfully opened, False otherwise
        """

        pair_manager: PairManagerDict = self.pair_manager_list[pair]
        pair_manager["position_driver"] = PositionDriver(self.ftx_rest_api,
                                                         POSITION_DRIVER_WORKER_SLEEP_TIME_BETWEEN_LOOPS)

        response = self.ftx_rest_api.get("wallet/balances")
        wallets = [format_wallet_raw_data(wallet) for wallet in response if
                   wallet["coin"] == 'USD' and wallet["free"] >= 10]

        if len(wallets) != 1:
            logging.info(f"Market:{pair}, Can't open a position :/. Wallet USD collateral low")
            return False  # Funds are not sufficient

        wallet: WalletDict = wallets[0]
        logging.info(f"Market:{pair}, wallet: {str(wallet)}")

        position_price = wallet["free"] * POSITION_LEVERAGE

        if position_price + self.total_invested > wallet["free"]:
            logging.info(f"Market:{pair}, Can't open a position :/. Opened positions would exceed wallet balance")
            return False

        # Retrieve market data
        logging.info("Retrieving market price")
        response = self.ftx_rest_api.get(f"markets/{pair}")
        logging.info(f"FTX API response: {str(response)}")

        market_data: MarketDataDict = format_market_raw_data(response)

        position_size = math.floor(position_price / market_data["ask"]) - \
            math.floor(position_price / market_data["ask"]) % market_data["size_increment"]

        # Configure position settings

        openings = [{
            "price": None,
            "size": position_size,
            "type": OrderTypeEnum.MARKET
        }]

        sl: TriggerOrderConfigDict = {
            "size": position_size,
            "type": TriggerOrderTypeEnum.STOP,
            "reduce_only": True,
            "trigger_price": market_data["ask"] - market_data["ask"] * STOP_LOSS_PERCENTAGE / 100,
            "order_price": None,
            "trail_value": None
        }

        trailing_stop: TriggerOrderConfigDict = {
            "size": position_size,
            "type": TriggerOrderTypeEnum.TRAILING_STOP,
            "reduce_only": True,
            "trigger_price": None,
            "order_price": None,
            "trail_value": market_data["ask"] * TRAILING_STOP_PERCENTAGE / 100 * -1
        }

        position_config: PositionConfigDict = {
            "openings": openings,
            "trigger_orders": [sl, trailing_stop],
            "max_open_duration": POSITION_MAX_OPEN_DURATION
        }

        pair_manager["position_driver"].open_position(pair, SideEnum.BUY, position_config)
        self.total_invested = self.total_invested + position_price
        pair_manager["invested"] = position_price
        return True
