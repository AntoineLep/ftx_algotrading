import logging
import math
import time

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
from core.strategy.strategy import Strategy
from core.trading.position_driver import PositionDriver
from strategies.multi_coin_abnormal_volumes_tracker.models.pair_manager_dict import PairManagerDict
from tools.utils import format_wallet_raw_data, format_market_raw_data

PAIRS_TO_TRACK = [
    "BTC-PERP", "ETH-PERP", "SOL-PERP", "LUNA-PERP", "WAVES-PERP", "GMT-PERP", "AXS-PERP", "AVAX-PERP", "ZIL-PERP",
    "RUNE-PERP", "NEAR-PERP", "AAVE-PERP", "APE-PERP", "ETC-PERP", "FIL-PERP", "ATOM-PERP", "LOOKS-PERP", "FTM-PERP",
    "ADA-PERP", "XRP-PERP", "CHZ-PERP", "LRC-PERP", "DOT-PERP", "VET-PERP", "GALA-PERP", "SUSHI-PERP", "FTT-PERP",
    "LINK-PERP", "MATIC-PERP", "SRM-PERP", "BNB-PERP", "SAND-PERP", "COMP-PERP", "EOS-PERP", "KNC-PERP", "LTC-PERP",
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
    "TONCOIN-PERP", "POLIS-PERP", "REEF-PERP", "FXS-PERP", "STEP-PERP", "FIDA-PERP", "HUM-PERP", "HT-PERP", "FLM-PERP",
    "BNT-PERP", "AMPL-PERP", "XAUT-PERP", "PROM-PERP", "KSOS-PERP", "BIT-PERP", "BOBA-PERP", "DAWN-PERP", "RAMP-PERP",
    "YFII-PERP", "OXY-PERP", "SOS-PERP", "LEO-PERP", "ORBS-PERP", "MTA-PERP", "TRYB-PERP", "MCB-PERP", "EDEN-PERP",
    "MNGO-PERP", "CONV-PERP", "BAO-PERP", "SECO-PERP", "CEL-PERP", "HOLY-PERP", "ROOK-PERP", "MER-PERP", "TULIP-PERP",
    "ASD-PERP", "KIN-PERP", "MOB-PERP", "BRZ-PERP", "SRN-PERP", "BTT-PERP", "MEDIA-PERP"
]

# FTX api rate limit is 10 requests per second
TIME_TO_SLEEP_BETWEEN_TIMEFRAME_LAUNCH = 0.25  # Sleeping 250 ms will avoid errors with a reasonable tolerance

LONG_MA_VOLUME_DEPTH = 100  # The number of candles to be used as volume comparison base
SHORT_MA_VOLUME_DEPTH = 5  # The number of candles used to compare volumes on (must be < than LONG_MA_VOLUME_DEPTH)

# Factor by which the SHORT_MA_VOLUME_DEPTH volumes must be higher than LONG_MA_VOLUME_DEPTH volumes
VOLUME_CHECK_FACTOR_SIZE = 20

MINIMUM_AVERAGE_VOLUME = 20000  # Minimum average volume to pass validation (avoid unsellable coin)
MINIMUM_PRICE_VARIATION = 2  # Percentage of variation a coin must have during its last SHORT_MA_VOLUME_DEPTH candles
POSITION_DRIVER_WORKER_SLEEP_TIME_BETWEEN_LOOPS = 120  # When a position driver is running, check market every x sec
WALLET_POSITION_MAX_RATIO = 1/10  # Wallet position price max ratio
MINIMUM_OPENABLE_POSITION_PRICE = 50  # Don't open a position for less than this amount
TRAILING_STOP_PERCENTAGE = 8  # Trailing stop percentage
POSITION_MAX_OPEN_DURATION = 4 * 60 * 60
JAIL_DURATION = 60 * 60  # Time for wish a coin can't be re bought after a position is closed on it


class MultiCoinAbnormalVolumesTracker(Strategy):
    """Multi coin abnormal volumes tracker"""

    def __init__(self):
        """The multi coin abnormal volumes tracker strategy constructor"""

        logging.info("MultiCoinAbnormalVolumesTracker run strategy")
        super(MultiCoinAbnormalVolumesTracker, self).__init__()

        self.ftx_rest_api: FtxRestApi = FtxRestApi()
        self.pair_manager_list = {}  # { [pair]: pair_manager }

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
                "jail_start_timestamp": 0
            }

            self.pair_manager_list[pair_to_track] = pair_manager
            time.sleep(TIME_TO_SLEEP_BETWEEN_TIMEFRAME_LAUNCH)

    def before_loop(self) -> None:
        pass

    def loop(self) -> None:
        """The strategy core"""

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

    def after_loop(self) -> None:
        time.sleep(10)

    def cleanup(self) -> None:
        """Clean strategy execution"""
        logging.info("MultiCoinAbnormalVolumesTracker cleanup")

        i = 0
        for pair_to_track in PAIRS_TO_TRACK:
            i += 1
            logging.info(f"Stopping time frame acquisition on pair {i} of {len(PAIRS_TO_TRACK)}: {pair_to_track}")
            self.pair_manager_list[pair_to_track]["crypto_pair_manager"].stop_all_time_frame_acq()

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
            pair_manager["last_position_driver_state"] = PositionStateEnum.NOT_OPENED
            pair_manager["jail_start_timestamp"] = int(time.time())

        # Coin is in jail after a position was closed
        if int(time.time()) < pair_manager["jail_start_timestamp"] + JAIL_DURATION:
            return False  # Skip this coin

        stock_data_manager = pair_manager["crypto_pair_manager"].get_time_frame(60).stock_data_manager

        # Not enough data
        if len(stock_data_manager.stock_data_list) < LONG_MA_VOLUME_DEPTH:
            return False

        # Check average LONG_MA_VOLUME_DEPTH (lma) candles volume is VOLUME_CHECK_FACTOR_SIZE times more
        # than the average SHORT_MA_VOLUME_DEPTH (sma)
        lma_sum_volume = sum([d.volume for d in stock_data_manager.stock_data_list[-LONG_MA_VOLUME_DEPTH:]])
        lma_avg_volume = lma_sum_volume / LONG_MA_VOLUME_DEPTH

        sma_sum_volume = sum([d.volume for d in stock_data_manager.stock_data_list[-SHORT_MA_VOLUME_DEPTH:]])
        sma_avg_volume = sma_sum_volume / SHORT_MA_VOLUME_DEPTH

        # If recent volumes are not VOLUME_CHECK_FACTOR_SIZE time more than old volumes
        if sma_avg_volume / lma_avg_volume < VOLUME_CHECK_FACTOR_SIZE:
            return False  # Skip this coin

        logging.info(f"Market:{pair}, volume factor check passes !"
                     f"{sma_avg_volume} > {lma_avg_volume} * {VOLUME_CHECK_FACTOR_SIZE}")

        individual_candle_volume_check = True
        for i in range(1, SHORT_MA_VOLUME_DEPTH + 1):
            individual_candle_volume_check = stock_data_manager.stock_data_list[-i].volume > lma_avg_volume
            if individual_candle_volume_check is False:
                break

        if individual_candle_volume_check is False:
            logging.info(f"Market:{pair}, volume individual candle check fail !")
            return False  # Skip this coin

        # Check the volume are "good" (avoid unsellable coins)
        if sma_avg_volume < MINIMUM_AVERAGE_VOLUME:
            logging.info(f"Market:{pair}, volume minimum value check fail !"
                         f"{sma_avg_volume} < {MINIMUM_AVERAGE_VOLUME}")
            return False  # Skip this coin

        logging.info(f"Market:{pair}, Volume minimum value check passes !"
                     f"{sma_avg_volume} >= {MINIMUM_AVERAGE_VOLUME}")

        # Check the price is up from at least MINIMUM_PRICE_VARIATION %
        candle_before = stock_data_manager.stock_data_list[-(SHORT_MA_VOLUME_DEPTH + 1)]
        last_candle = stock_data_manager.stock_data_list[-1]

        if last_candle.close_price < candle_before.open_price * (1 + MINIMUM_PRICE_VARIATION / 100):
            logging.info(f"Market:{pair}, price minimum check fail !"
                         f"{last_candle.close_price} < {candle_before.open_price} * {MINIMUM_PRICE_VARIATION}%")
            return False  # Skip this coin

        logging.info(f"Market:{pair}, price minimum check passes !"
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
        position_price = math.floor(wallet["free"]) * WALLET_POSITION_MAX_RATIO

        if position_price < MINIMUM_OPENABLE_POSITION_PRICE:
            logging.info(f"Market:{pair}, Can't open a position :/. Wallet USD collateral low")
            return False  # Funds are not sufficient

        # Retrieve market data
        logging.info("Retrieving market price")
        response = self.ftx_rest_api.get(f"markets/{pair}")
        logging.info(f"FTX API response: {str(response)}")

        market_data: MarketDataDict = format_market_raw_data(response)

        position_size = math.floor(position_price / response["ask"]) - \
            math.floor(position_price / response["ask"]) % market_data["sizeIncrement"]

        # Configure position settings

        openings = [{
            "price": None,
            "size": position_size,
            "type": OrderTypeEnum.MARKET
        }]

        trailing_stop: TriggerOrderConfigDict = {
            "size": position_size,
            "type": TriggerOrderTypeEnum.TRAILING_STOP,
            "reduce_only": True,
            "trigger_price": None,
            "order_price": None,
            "trail_value": response["ask"] * TRAILING_STOP_PERCENTAGE / 100 * -1
        }

        position_config: PositionConfigDict = {
            "openings": openings,
            "trigger_orders": [trailing_stop],
            "max_open_duration": POSITION_MAX_OPEN_DURATION
        }

        pair_manager["position_driver"].open_position(pair, SideEnum.BUY, position_config)
        return True
