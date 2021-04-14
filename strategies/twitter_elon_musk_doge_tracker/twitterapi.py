import requests

import config.twitterconfig as twitter_config


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

        url = "https://api.twitter.com/2/tweets/search/recent?query={}".format(query)

        if tweet_fields is not None:
            url += "&tweet.fields={}".format(tweet_fields)

        if since_id is not None:
            url += "&since_id={}".format(since_id)

        headers = {"Authorization": "Bearer {}".format(twitter_config.api["bearer_token"])}

        response = requests.request("GET", url, headers=headers)

        if response.status_code != 200:
            raise Exception(response.status_code, response.text)
        return response.json()
