import json
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
from strategies.twitter_elon_musk_doge_tracker.enums.probability_enum import ProbabilityEnum
from strategies.twitter_elon_musk_doge_tracker.order_decision_maker import OrderDecisionMaker
from strategies.twitter_elon_musk_doge_tracker.twitter_api import TwitterApi
from tools.utils import format_wallet_raw_data, format_market_raw_data

DEFAULT_DECIDING_TIMEOUT = 30  # Time for taking the decision to buy DOGE according to volume check

SAFE_LEVERAGE = 8  # Will be used in case of TWITTER_ACCOUNT answering to someone
BASE_LEVERAGE = 15  # Will be used otherwise

# First take profit
TP1_TARGET_PERCENTAGE = 5
TP1_SIZE_RATIO = 0.3

# Second take profit
TP2_TARGET_PERCENTAGE = 8.5
TP2_SIZE_RATIO = 0.4

# Last take profit
TP3_TARGET_PERCENTAGE = 12
# TP3_SIZE_RATIO Will be filled with remaining position size

# Stop loss
SL_PERCENTAGE = 0.5

MAX_OPEN_DURATION = 60 * 4

POSITION_MAX_PRICE = 100000  # Won't be able to open a position with usd price higher than this
SUB_POSITION_MAX_PRICE = 20000  # Maximum position price before splitting position order into smaller ones

TWITTER_ACCOUNT = "elonmusk"
BYPASS_DECISION_MAKER = False

_SLEEP_TIME_BETWEEN_LOOPS = 5


class TwitterElonMuskDogeTracker(Strategy):
    """The Elon Musk tweets will make us rich !!"""

    def __init__(self):
        """The Twitter Elon Musk Doge Tracker constructor"""

        logging.info("TwitterElonMuskDogeTracker run strategy")
        super(TwitterElonMuskDogeTracker, self).__init__()

        self.ftx_rest_api: FtxRestApi = FtxRestApi()

        # Init local values
        self.last_tweet: dict = {"id": None, "text": ""}
        self.new_tweet: bool = False
        self.first_loop: bool = True
        self.last_tweet_doge_oriented_probability: ProbabilityEnum = ProbabilityEnum.NOT_PROBABLE
        self.deciding_timeout = DEFAULT_DECIDING_TIMEOUT
        self.is_deciding = False

        # Init stock acquisition / order decision maker / position driver
        self.doge_manager: CryptoPairManager = CryptoPairManager("DOGE-PERP", self.ftx_rest_api)
        self.doge_manager.add_time_frame(15)
        self.doge_manager.start_all_time_frame_acq()
        self.order_decision_maker: OrderDecisionMaker = OrderDecisionMaker(
            self.doge_manager.get_time_frame(15).stock_data_manager)
        self.position_driver: PositionDriver = PositionDriver(self.ftx_rest_api)

    def before_loop(self) -> None:
        # Init default values
        self.new_tweet = False

    def loop(self) -> None:
        """The strategy core"""

        if not self.is_deciding and self.position_driver.position_state == PositionStateEnum.NOT_OPENED:
            self.last_tweet_doge_oriented_probability = ProbabilityEnum.NOT_PROBABLE
            try:
                self.fetch_tweets()
            except Exception as e:
                logging.error("An error occurred when fetching tweets")
                logging.error(e)
                logging.info("Sleeping for 15 sec")
                time.sleep(15)
                return

            if self.new_tweet and not self.first_loop:
                # Start deciding process
                self.is_deciding = True
                self.deciding_timeout = DEFAULT_DECIDING_TIMEOUT
                logging.info("Starting to make a decision regarding the new tweet")

        decision_taken = False
        if self.is_deciding:
            if self.order_decision_maker.decide(self.last_tweet_doge_oriented_probability) or BYPASS_DECISION_MAKER:
                logging.info("Decision has been made to buy ! Let's open the position")
                decision_taken = True
                self.deciding_timeout = 0
                self.open_position()
            else:
                self.deciding_timeout -= _SLEEP_TIME_BETWEEN_LOOPS

        # Update values before next loop
        if self.deciding_timeout <= 0:
            if self.is_deciding:
                if decision_taken is False:
                    logging.info("Decision making timed out")

                self.is_deciding = False

    def after_loop(self) -> None:
        self.first_loop = False
        time.sleep(_SLEEP_TIME_BETWEEN_LOOPS)  # Every good warriors needs to rest sometime

    def cleanup(self) -> None:
        """Clean strategy execution"""

        logging.info("TwitterElonMuskDogeTracker cleanup")
        self.doge_manager.stop_all_time_frame_acq()

    def open_position(self):
        """Compute position subsets, tps, and sl. Then, open a position"""

        if self.position_driver.position_state == PositionStateEnum.NOT_OPENED:
            response = self.ftx_rest_api.get("wallet/balances")
            wallets = [format_wallet_raw_data(wallet) for wallet in response if
                       wallet["coin"] == 'USD' and wallet["free"] >= 10]

            if len(wallets) == 1:
                wallet: WalletDict = wallets[0]
                applied_leverage = SAFE_LEVERAGE if \
                    self.last_tweet_doge_oriented_probability == ProbabilityEnum.NOT_PROBABLE else BASE_LEVERAGE
                position_price = min(math.floor(wallet["free"]) * applied_leverage, POSITION_MAX_PRICE)

                # Retrieve market data
                logging.info("Retrieving market price")
                response = self.ftx_rest_api.get(f"markets/DOGE-PERP")
                logging.info(f"FTX API response: {str(response)}")

                market_data: MarketDataDict = format_market_raw_data(response)
                position_size = math.floor(position_price / market_data["ask"])

                openings = []

                while position_price > 1:
                    sub_position_price = position_price if position_price < SUB_POSITION_MAX_PRICE \
                        else SUB_POSITION_MAX_PRICE
                    sub_position_size = math.floor(sub_position_price / market_data["ask"])

                    openings.append({
                        "price": None,
                        "size": sub_position_size,
                        "type": OrderTypeEnum.MARKET
                    })

                    position_price -= sub_position_price

                tp1: TriggerOrderConfigDict = {
                    "size": position_size * TP1_SIZE_RATIO,
                    "type": TriggerOrderTypeEnum.TAKE_PROFIT,
                    "reduce_only": True,
                    "trigger_price": market_data["ask"] + market_data["ask"] * TP1_TARGET_PERCENTAGE / 100,
                    "order_price": None,
                    "trail_value": None
                }

                tp2: TriggerOrderConfigDict = {
                    "size": position_size * TP2_SIZE_RATIO,
                    "type": TriggerOrderTypeEnum.TAKE_PROFIT,
                    "reduce_only": True,
                    "trigger_price": market_data["ask"] + market_data["ask"] * TP2_TARGET_PERCENTAGE / 100,
                    "order_price": None,
                    "trail_value": None
                }

                tp3: TriggerOrderConfigDict = {
                    "size": position_size - tp1["size"] - tp2["size"],
                    "type": TriggerOrderTypeEnum.TAKE_PROFIT,
                    "reduce_only": True,
                    "trigger_price": market_data["ask"] + market_data["ask"] * TP3_TARGET_PERCENTAGE / 100,
                    "order_price": None,
                    "trail_value": None
                }

                sl: TriggerOrderConfigDict = {
                    "size": position_size,
                    "type": TriggerOrderTypeEnum.STOP,
                    "reduce_only": True,
                    "trigger_price": market_data["ask"] - market_data["ask"] * SL_PERCENTAGE / 100,
                    "order_price": None,
                    "trail_value": None
                }

                position_config: PositionConfigDict = {
                    "openings": openings,
                    "trigger_orders": [tp1, tp2, tp3, sl],
                    "max_open_duration": MAX_OPEN_DURATION
                }

                self.position_driver.open_position("DOGE-PERP", SideEnum.BUY, position_config)

    def fetch_tweets(self):
        """Fetch tweets"""

        logging.info("Fetching tweets...")

        # Get tweets since last stored one
        tweets = TwitterApi.search_tweets(
            query=f"from:{TWITTER_ACCOUNT}",
            tweet_fields="author_id,text,attachments",
            since_id=self.last_tweet["id"]
        )

        # New tweet !
        if tweets["meta"]["result_count"] > 0:
            self.new_tweet = True
            self.last_tweet = tweets["data"][0]  # Store it

            # If it's not the first loop, then process the tweet
            if not self.first_loop:
                self.process_last_tweet()

    def process_last_tweet(self):
        """We've found a tweet to process"""

        last_tweet = self.last_tweet
        logging.info("Processing new tweet:")
        logging.info(json.dumps(last_tweet, indent=4, sort_keys=True))

        doge_related_words = ["doge", "dog", "shiba"]
        probable_related_words = ["moon", "mars", "hodl", "hold", "coin"]
        last_tweet["text"] = last_tweet["text"].lower()

        if str(last_tweet["text"]).startswith("@"):
            logging.info("Answering someone, can have weird market reaction")
            self.last_tweet_doge_oriented_probability = ProbabilityEnum.NOT_PROBABLE
        elif str(last_tweet["text"]).startswith("rt @"):
            logging.info("Retweeting, can have weird market reaction")
            self.last_tweet_doge_oriented_probability = ProbabilityEnum.UNKNOWN
        else:
            tweet_contains_attachment = "attachments" in last_tweet
            tweet_contains_text = " " in last_tweet["text"]
            tweet_contains_doge_related_words = any(word in last_tweet["text"] for word in doge_related_words)
            tweet_contains_probable_related_words = any(word in last_tweet["text"] for word in probable_related_words)

            if tweet_contains_doge_related_words:  # Doge related text
                self.last_tweet_doge_oriented_probability = ProbabilityEnum.PROBABLE
            elif tweet_contains_probable_related_words:
                self.last_tweet_doge_oriented_probability = ProbabilityEnum.MAYBE_PROBABLE
            elif (tweet_contains_attachment and tweet_contains_text) or tweet_contains_attachment:
                # Image + text / image
                self.last_tweet_doge_oriented_probability = ProbabilityEnum.MAYBE_PROBABLE
            else:  # Text not related with doge
                self.last_tweet_doge_oriented_probability = ProbabilityEnum.UNKNOWN
