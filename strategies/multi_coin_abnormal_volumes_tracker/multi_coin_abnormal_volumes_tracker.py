import logging
import time
import math

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
    "MEDIA-PERP", "TRYB-PERP", "MCB-PERP", "ORBS-PERP", "HOLY-PERP", "BNT-PERP", "AXS-PERP", "CRV-PERP", "FIL-PERP",
    "DRGN-PERP", "MTA-PERP", "CELO-PERP", "BRZ-PERP", "BAO-PERP", "CEL-PERP", "SRN-PERP", "LTC-PERP", "ALT-PERP",
    "MNGO-PERP", "YFII-PERP", "BAND-PERP", "STMX-PERP", "ROOK-PERP", "MVDA10-PERP", "POLIS-PERP", "ALGO-PERP",
    "HT-PERP", "ALPHA-PERP", "PUNDIX-PERP", "CONV-PERP", "SKL-PERP", "EDEN-PERP", "AMPL-PERP", "RNDR-PERP", "ETC-PERP",
    "TOMO-PERP", "MID-PERP", "OKB-PERP", "SCRT-PERP", "FLM-PERP", "DAWN-PERP", "BAL-PERP", "XTZ-PERP", "KNC-PERP",
    "ZIL-PERP", "EXCH-PERP", "C98-PERP", "PROM-PERP", "ALCX-PERP", "PRIV-PERP", "DENT-PERP", "GALA-PERP", "ALGO-PERP",
    "PERP-PERP", "ONT-PERP", "LINA-PERP", "HUM-PERP", "HOT-PERP", "RAMP-PERP", "DASH-PERP", "EOS-PERP", "DYDX-PERP",
    "TRU-PERP", "TULIP-PERP", "BADGER-PERP", "ZRX-PERP", "SOS-PERP", "DODO-PERP", "BIT-PERP", "SPELL-PERP", "SNX-PERP",
    "BOBA-PERP", "TLM-PERP", "XEM-PERP", "KAVA-PERP", "HBAR-PERP", "REEF-PERP", "REN-PERP", "ICP-PERP", "LOOKS-PERP",
    "AUDIO-PERP", "KIN-PERP", "CLV-PERP", "SC-PERP", "STX-PERP", "ICX-PERP", "SHIT-PERP", "BCH-PERP", "LRC-PERP",
    "TONCOIN-PERP", "BAT-PERP", "IOTA-PERP", "ATLAS-PERP", "XMR-PERP", "LEO-PERP", "ENS-PERP", "AR-PERP", "FIDA-PERP",
    "CVC-PERP", "DEFI-PERP", "SHIB-PERP", "RSR-PERP", "STEP-PERP", "CREAM-PERP", "PEOPLE-PERP", "ONE-PERP", "RAY-PERP",
    "RON-PERP", "NEO-PERP", "ALICE-PERP", "OXY-PERP", "OMG-PERP", "NEAR-PERP", "AGLD-PERP", "ENJ-PERP", "AAVE-PERP",
    "CAKE-PERP", "KSM-PERP", "STORJ-PERP", "HNT-PERP", "COMP-PERP", "YFI-PERP", "SXP-PERP", "XLM-PERP", "SRM-PERP",
    "SLP-PERP", "THETA-PERP", "ROSE-PERP", "MKR-PERP", "QTUM-PERP", "1INCH-PERP", "TRX-PERP", "EGLD-PERP", "CRO-PERP",
    "WAVES-PERP", "GRT-PERP", "CHR-PERP", "MAPS-PERP", "CHZ-PERP", "VET-PERP", "FLOW-PERP", "ZEC-PERP", "RUNE-PERP",
    "MER-PERP", "MTL-PERP"
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
            print(f"Initialising pair {i} of {len(PAIRS_TO_TRACK)}: {pair_to_track}")
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

        try:
            # For each coin
            for pair_to_track in PAIRS_TO_TRACK:
                pair_manager: PairManagerDict = self.pair_manager_list[pair_to_track]

                # Check the coin is not currently bought (position driver running)
                if pair_manager["position_driver"] is not None \
                        and pair_manager["position_driver"].position_state is PositionStateEnum.OPENED:
                    continue  # Skip this coin

                # First time we loop after a position was closed
                if pair_manager["last_position_driver_state"] == PositionStateEnum.OPENED:
                    pair_manager["last_position_driver_state"] = PositionStateEnum.NOT_OPENED
                    pair_manager["jail_start_timestamp"] = int(time.time())

                # Coin is in jail after a position was closed
                if int(time.time()) < pair_manager["jail_start_timestamp"] + JAIL_DURATION:
                    continue  # Skip this coin

                stock_data_manager = pair_manager["crypto_pair_manager"].get_time_frame(60).stock_data_manager

                # Not enough data
                if len(stock_data_manager.stock_data_list) < LONG_MA_VOLUME_DEPTH:
                    continue

                # Check average LONG_MA_VOLUME_DEPTH (lma) candles volume is VOLUME_CHECK_FACTOR_SIZE times more
                # than the average SHORT_MA_VOLUME_DEPTH (sma)
                lma_sum_volume = sum([d.volume for d in stock_data_manager.stock_data_list[-LONG_MA_VOLUME_DEPTH:]])
                lma_avg_volume = lma_sum_volume / LONG_MA_VOLUME_DEPTH

                sma_sum_volume = sum([d.volume for d in stock_data_manager.stock_data_list[-SHORT_MA_VOLUME_DEPTH:]])
                sma_avg_volume = sma_sum_volume / SHORT_MA_VOLUME_DEPTH

                # If recent volumes are not VOLUME_CHECK_FACTOR_SIZE time more than old volumes
                if sma_avg_volume / lma_avg_volume < VOLUME_CHECK_FACTOR_SIZE:
                    continue  # Skip this coin

                logging.info(f"Market:{pair_to_track}, volume factor check passes !"
                             f"{sma_avg_volume} > {lma_avg_volume} * {VOLUME_CHECK_FACTOR_SIZE}")

                # Check the volume are "good" (avoid unsellable coins)
                if sma_avg_volume < MINIMUM_AVERAGE_VOLUME:
                    logging.info(f"Market:{pair_to_track}, volume minimum value check fail !"
                                 f"{sma_avg_volume} < {MINIMUM_AVERAGE_VOLUME}")
                    continue  # Skip this coin

                logging.info(f"Market:{pair_to_track}, Volume minimum value check passes !"
                             f"{sma_avg_volume} >= {MINIMUM_AVERAGE_VOLUME}")

                # Check the price is up from at least MINIMUM_PRICE_VARIATION %
                candle_before = stock_data_manager.stock_data_list[-(SHORT_MA_VOLUME_DEPTH + 1)]
                last_candle = stock_data_manager.stock_data_list[-1]

                if last_candle.close_price < candle_before.open_price * (1 + MINIMUM_PRICE_VARIATION / 100):
                    logging.info(f"Market:{pair_to_track}, price minimum check fail !"
                                 f"{last_candle.close_price} < {candle_before.open_price} * {MINIMUM_PRICE_VARIATION}%")
                    continue  # Skip this coin

                logging.info(f"Market:{pair_to_track}, price minimum check passes !"
                             f"{last_candle.close_price} >= {candle_before.open_price} * {MINIMUM_PRICE_VARIATION}%")

                logging.info(f"Market:{pair_to_track}, all checks passed ! Let's buy this :)")

                pair_manager["position_driver"] = PositionDriver(self.ftx_rest_api,
                                                                 POSITION_DRIVER_WORKER_SLEEP_TIME_BETWEEN_LOOPS)

                response = self.ftx_rest_api.get("wallet/balances")
                wallets = [format_wallet_raw_data(wallet) for wallet in response if
                           wallet["coin"] == 'USD' and wallet["free"] >= 10]

                if len(wallets) != 1:
                    logging.info(f"Market:{pair_to_track}, Can't open a position :/. Wallet USD collateral low")
                    continue  # Funds are not sufficient

                wallet: WalletDict = wallets[0]
                position_price = math.floor(wallet["free"]) / WALLET_POSITION_MAX_RATIO

                # Retrieve market data
                logging.info("Retrieving market price")
                response = self.ftx_rest_api.get(f"markets/{pair_to_track}")
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

                pair_manager["position_driver"].open_position(pair_to_track, SideEnum.BUY, position_config)
                pair_manager["last_position_driver_state"] = PositionStateEnum.OPENED

        except Exception as e:
            logging.error(e)

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
