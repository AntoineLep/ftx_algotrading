import logging
import time
import json
import threading

from core.strategy.strategy import Strategy
from strategies.twitter_elon_musk_doge_tracker.twitter_api import TwitterApi
from core.ftx.rest.ftx_rest_api import FtxRestApi
from strategies.twitter_elon_musk_doge_tracker.probability import Probability
from core.sotck.crypto_pair_manager import CryptoPairManager


class TwitterElonMuskDogeTracker(Strategy):
    """The Elon Musk tweets will make us rich !!"""
    doge_manager: CryptoPairManager

    def __init__(self):
        """The Twitter Elon Musk Doge Tracker constructor"""
        super(TwitterElonMuskDogeTracker, self).__init__()
        self.twitter_api = TwitterApi()
        self.ftx_rest_api = FtxRestApi()
        self.last_tweet = {"id": None, "text": ""}
        self.last_tweet_doge_oriented_probability = Probability.NOT_PROBABLE
        self.first_loop = True
        self.lock = threading.Lock()
        self.doge_manager = None

    def startup(self) -> None:
        """Strategy initialisation"""

        logging.info("TwitterElonMuskDogeTracker startup")
        self.doge_manager = CryptoPairManager("DOGE-PERP", self.ftx_rest_api, self.lock)
        self.doge_manager.add_time_frame(15)
        self.doge_manager.start_all_time_frame_acq()

    def run_strategy(self) -> None:
        """The strategy core"""
        logging.info("TwitterElonMuskDogeTracker run_strategy")

        while True:
            # Init default values
            self.last_tweet_doge_oriented_probability = Probability.NOT_PROBABLE
            self.fetch_tweets()

            if self.last_tweet_doge_oriented_probability is not Probability.NOT_PROBABLE:
                # TODO:
                # create an order decision maker
                # will have to take a decision within a given time, given a dict of indicators
                # check_volumes (True / False), probability
                #
                # create a position driver
                # will open a position and manage it according to a dict of config
                # config fields will contain: pair, leverage, tp, sl, max_exposition_time (in sec)
                pass

            self.first_loop = False
            time.sleep(5)  # Every good warriors needs to rest sometime

    def fetch_tweets(self):
        """Fetch tweets"""
        # Get tweets since last stored one
        tweets = self.twitter_api.search_tweets(
            query="from:TuxdisTV",
            tweet_fields="author_id,text,attachments",
            since_id=self.last_tweet["id"]
        )

        # New tweet !
        if tweets["meta"]["result_count"] > 0:
            self.last_tweet = tweets["data"][0]  # Store it

            # If it's not the first loop, then process the tweet
            if not self.first_loop:
                self.process_last_tweet()

    def process_last_tweet(self):
        """We've found a tweet to process"""
        last_tweet = self.last_tweet
        logging.info("Processing new tweet:")
        logging.info(json.dumps(last_tweet, indent=4, sort_keys=True))

        doge_related_words = ['doge', 'moon', 'dog', 'shiba']
        last_tweet["text"] = last_tweet["text"].lower()

        tweet_contains_attachment = "attachments" in last_tweet
        tweet_contains_text = " " in last_tweet["text"]
        tweet_contains_doge_related_words = any(word in last_tweet["text"] for word in doge_related_words)

        if tweet_contains_doge_related_words:  # Doge related text
            self.last_tweet_doge_oriented_probability = Probability.PROBABLE
        elif (tweet_contains_attachment and tweet_contains_text) or tweet_contains_attachment:  # Image + text / image
            self.last_tweet_doge_oriented_probability = Probability.MAYBE_PROBABLE
        else:  # Text not related with doge
            self.last_tweet_doge_oriented_probability = Probability.NOT_PROBABLE

    def cleanup(self) -> None:
        """Clean strategy execution"""
        logging.info("TwitterElonMuskDogeTracker cleanup")
        self.doge_manager.stop_all_time_frame_acq()

