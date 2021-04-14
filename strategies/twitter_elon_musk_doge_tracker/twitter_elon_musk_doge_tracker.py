import logging
import time
import json

from core.strategy import Strategy
from strategies.twitter_elon_musk_doge_tracker.twitterapi import TwitterApi
from strategies.twitter_elon_musk_doge_tracker.probability import Probability


class TwitterElonMuskDogeTracker(Strategy):
    """The Elon Musk tweets will make us rich !!"""

    def __init__(self):
        """The Twitter Elon Musk Doge Tracker constructor"""
        super(TwitterElonMuskDogeTracker, self).__init__()
        self._twitter_api = TwitterApi()
        self._last_tweet = {"id": None, "text": ""}
        self._last_tweet_doge_oriented_probability = Probability.NOT_PROBABLE

    def startup(self) -> None:
        """Strategy initialisation"""
        logging.info("TwitterElonMuskDogeTracker startup")

    def run_strategy(self) -> None:
        """The strategy core"""
        logging.info("TwitterElonMuskDogeTracker run_strategy")

        first_loop = True

        while True:
            # Init default values
            self._last_tweet_doge_oriented_probability = Probability.NOT_PROBABLE

            # Get tweets since last stored one
            tweets = self._twitter_api.search_tweets(
                query="from:TuxdisTV",
                tweet_fields="author_id,text,attachments",
                since_id=self._last_tweet["id"]
                )

            # New tweet !
            if tweets["meta"]["result_count"] > 0:
                self._last_tweet = tweets["data"][0]  # Store it

                # If it's not the first loop, then process the tweet
                if not first_loop:
                    self.process_last_tweet()

                if self._last_tweet_doge_oriented_probability is not Probability.NOT_PROBABLE:
                    # TODO:
                    # create an order decision maker
                    # create a position driver
                    pass

            first_loop = False
            time.sleep(5)  # Every good warriors needs to rest sometime

    def process_last_tweet(self):
        """We've found a tweet to process"""
        last_tweet = self._last_tweet
        logging.info("Processing new tweet:")
        logging.info(json.dumps(last_tweet, indent=4, sort_keys=True))

        doge_related_words = ['doge', 'moon', 'dog', 'shiba']
        last_tweet["text"] = last_tweet["text"].lower()

        tweet_contains_attachment = "attachments" in last_tweet
        tweet_contains_text = " " in last_tweet["text"]
        tweet_contains_doge_related_words = any(word in last_tweet["text"] for word in doge_related_words)

        if tweet_contains_doge_related_words:  # Doge related text
            self._last_tweet_doge_oriented_probability = Probability.PROBABLE
        elif (tweet_contains_attachment and tweet_contains_text) or tweet_contains_attachment:  # Image + text / image
            self._last_tweet_doge_oriented_probability = Probability.MAYBE_PROBABLE
        else:  # Text not related with doge
            self._last_tweet_doge_oriented_probability = Probability.NOT_PROBABLE

    def cleanup(self) -> None:
        """Clean strategy execution"""
        logging.info("TwitterElonMuskDogeTracker cleanup")
