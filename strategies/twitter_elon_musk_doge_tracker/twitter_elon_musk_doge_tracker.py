import json
import logging
import threading
import time

from core.ftx.rest.ftx_rest_api import FtxRestApi
from core.stock.crypto_pair_manager import CryptoPairManager
from core.strategy.strategy import Strategy
from strategies.twitter_elon_musk_doge_tracker.enums.position_state_enum import PositionStateEnum
from strategies.twitter_elon_musk_doge_tracker.enums.probability_enum import ProbabilityEnum
from strategies.twitter_elon_musk_doge_tracker.order_decision_maker import OrderDecisionMaker
from strategies.twitter_elon_musk_doge_tracker.position_driver import PositionDriver
from strategies.twitter_elon_musk_doge_tracker.twitter_api import TwitterApi

DEFAULT_DECIDING_TIMEOUT = 75
SLEEP_TIME_BETWEEN_LOOPS = 5
LEVERAGE = 10
TP_TARGET_PERCENTAGE = 5
SL_TARGET_PERCENTAGE = 0.75
MAX_OPEN_DURATION = 60 * 5


class TwitterElonMuskDogeTracker(Strategy):
    """The Elon Musk tweets will make us rich !!"""

    def __init__(self):
        """The Twitter Elon Musk Doge Tracker constructor"""

        super(TwitterElonMuskDogeTracker, self).__init__()

        # Init API
        self.twitter_api: TwitterApi = TwitterApi()
        self.ftx_rest_api: FtxRestApi = FtxRestApi()

        # Init local values
        self.last_tweet: dict = {"id": None, "text": ""}
        self.new_tweet: bool = False
        self.first_loop: bool = True
        self.last_tweet_doge_oriented_probability: ProbabilityEnum = ProbabilityEnum.NOT_PROBABLE
        self.lock: threading.Lock = threading.Lock()

        # Init stock acquisition / order decision maker / position driver
        self.doge_manager: CryptoPairManager = CryptoPairManager("DOGE-PERP", self.ftx_rest_api, self.lock)
        self.doge_manager.add_time_frame(15)
        self.doge_manager.start_all_time_frame_acq()
        self.order_decision_maker: OrderDecisionMaker = OrderDecisionMaker(
            self.doge_manager.get_time_frame(15).stock_data_manager)
        self.position_driver: PositionDriver = PositionDriver(self.ftx_rest_api,
                                                              self.doge_manager.get_time_frame(15).stock_data_manager,
                                                              self.lock)

    def run_strategy(self) -> None:
        """The strategy core"""

        logging.info("TwitterElonMuskDogeTracker run_strategy")

        deciding_timeout = DEFAULT_DECIDING_TIMEOUT
        is_deciding = False

        while True:
            # Init default values
            self.new_tweet = False

            if not is_deciding and self.position_driver.position_state == PositionStateEnum.NOT_OPENED:
                self.last_tweet_doge_oriented_probability = ProbabilityEnum.NOT_PROBABLE
                try:
                    self.fetch_tweets()
                except Exception as e:
                    logging.info("An error occurred when fetching tweets")
                    logging.info(e)
                    logging.info("Sleeping for 60 sec")
                    time.sleep(60)
                    continue

                if self.new_tweet and not self.first_loop:
                    # Start deciding process
                    is_deciding = True
                    deciding_timeout = DEFAULT_DECIDING_TIMEOUT
                    logging.info("Starting to make a decision regarding the new tweet")

            if is_deciding:
                if self.order_decision_maker.decide(self.last_tweet_doge_oriented_probability):
                    logging.info("Decision has been made to buy ! Let's run the position driver")
                    deciding_timeout = 0
                    self.position_driver.open_position(LEVERAGE, TP_TARGET_PERCENTAGE, SL_TARGET_PERCENTAGE,
                                                       MAX_OPEN_DURATION)
                else:
                    deciding_timeout -= SLEEP_TIME_BETWEEN_LOOPS

            # Update values before next loop
            self.first_loop = False
            if deciding_timeout <= 0:
                if is_deciding:
                    logging.info("Decision making succeeded or timed out")
                    is_deciding = False

            time.sleep(SLEEP_TIME_BETWEEN_LOOPS)  # Every good warriors needs to rest sometime

    def fetch_tweets(self):
        """Fetch tweets"""

        logging.info("Fetching tweets...")

        # Get tweets since last stored one
        tweets = self.twitter_api.search_tweets(
            query="from:elonmusk",
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
        probable_related_words = ["moon", "mars", "hodl", "hold"]
        last_tweet["text"] = last_tweet["text"].lower()

        tweet_contains_attachment = "attachments" in last_tweet
        tweet_contains_text = " " in last_tweet["text"]
        tweet_contains_doge_related_words = any(word in last_tweet["text"] for word in doge_related_words)
        tweet_contains_probable_related_words = any(word in last_tweet["text"] for word in probable_related_words)

        if tweet_contains_doge_related_words:  # Doge related text
            self.last_tweet_doge_oriented_probability = ProbabilityEnum.PROBABLE
        elif tweet_contains_probable_related_words:
            self.last_tweet_doge_oriented_probability = ProbabilityEnum.MAYBE_PROBABLE
        elif (tweet_contains_attachment and tweet_contains_text) or tweet_contains_attachment:  # Image + text / image
            self.last_tweet_doge_oriented_probability = ProbabilityEnum.MAYBE_PROBABLE
        else:  # Text not related with doge
            self.last_tweet_doge_oriented_probability = ProbabilityEnum.NOT_PROBABLE

    def cleanup(self) -> None:
        """Clean strategy execution"""

        logging.info("TwitterElonMuskDogeTracker cleanup")
        self.doge_manager.stop_all_time_frame_acq()
