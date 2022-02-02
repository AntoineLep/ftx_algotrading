import logging
import time


from core.strategy.strategy import Strategy
from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.stock.crypto_pair_manager import CryptoPairManager


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


class MultiCoinAbnormalVolumesTracker(Strategy):
    """Multi coin abnormal volumes tracker"""

    def __init__(self):
        """The multi coin abnormal volumes tracker strategy constructor"""

        logging.info("MultiCoinAbnormalVolumesTracker run strategy")
        super(MultiCoinAbnormalVolumesTracker, self).__init__()

        self.ftx_rest_api: FtxRestApi = FtxRestApi()
        self.pair_manager_list = {}

        i = 0
        for pair_to_track in PAIRS_TO_TRACK:
            i += 1
            print(f"Initialising pair {i} of {len(PAIRS_TO_TRACK)}: {pair_to_track}")
            self.pair_manager_list[pair_to_track] = CryptoPairManager(pair_to_track, self.ftx_rest_api)
            self.pair_manager_list[pair_to_track].add_time_frame(60)
            self.pair_manager_list[pair_to_track].start_all_time_frame_acq()
            time.sleep(TIME_TO_SLEEP_BETWEEN_TIMEFRAME_LAUNCH)

    def before_loop(self) -> None:
        pass

    def loop(self) -> None:
        """The strategy core"""

        try:

            pass
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
            self.pair_manager_list[pair_to_track].stop_all_time_frame_acq()
