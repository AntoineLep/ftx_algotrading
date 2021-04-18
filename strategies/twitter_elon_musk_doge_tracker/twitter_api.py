import requests

import strategies.twitter_elon_musk_doge_tracker.config.private.twitter_config as twitter_config


class TwitterApi(object):

    @staticmethod
    def search_tweets(query, tweet_fields, since_id):
        """
        Call search tweet within twitter api
        :param query: "from:twitterdev -is:retweet"
        :param tweet_fields: "author_id,text,attachments"
        :param since_id: Last tweet id
        :return: Twitter response
        """

        url = f"https://api.twitter.com/2/tweets/search/recent?query={query}"

        if tweet_fields is not None:
            url += f"&tweet.fields={tweet_fields}"

        if since_id is not None:
            url += f"&since_id={since_id}"

        headers = {"Authorization": f"Bearer {twitter_config.api['bearer_token']}"}

        response = requests.request("GET", url, headers=headers)

        if response.status_code != 200:
            raise Exception(response.status_code, response.text)
        return response.json()
