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

        headers = TwitterApi._create_headers()

        response = requests.request("GET", url, headers=headers)

        if response.status_code != 200:
            raise Exception(response.status_code, response.text)
        return response.json()

    @staticmethod
    def _create_headers() -> dict:
        """
        Create authorization header with bearer token

        :return: Authorization header with bearer token
        """
        return {"Authorization": f"Bearer {twitter_config.api['bearer_token']}"}

    @staticmethod
    def get_rules() -> any:
        """
        Get rules

        :return: Rules
        """
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/stream/rules", headers=TwitterApi._create_headers()
        )
        if response.status_code != 200:
            raise Exception(f"Cannot get rules (HTTP {response.status_code}): {response.text}")
        return response.json()

    @staticmethod
    def delete_rules(rules) -> any:
        """
        Delete given rules

        :param rules: Rules to be deleted
        """
        if rules is None or "data" not in rules:
            return None

        ids = list(map(lambda rule: rule["id"], rules["data"]))
        payload = {"delete": {"ids": ids}}
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=TwitterApi._create_headers(),
            json=payload
        )
        if response.status_code != 200:
            raise Exception(f"Cannot delete rules (HTTP {response.status_code}): {response.text}")
        return response.json()

    @staticmethod
    def set_rules(rules: list) -> any:
        """
        Set rules

        :param rules: Rules to be set
        sample_rules = [
            {"value": "dog has:images", "tag": "dog pictures"},
            {"value": "cat has:images -grumpy", "tag": "cat pictures"},
        ]
        """
        # You can adjust the rules if needed

        payload = {"add": rules}
        response = requests.post(
            "https://api.twitter.com/2/tweets/search/stream/rules",
            headers=TwitterApi._create_headers(),
            json=payload,
        )
        if response.status_code != 201:
            raise Exception(f"Cannot add rules (HTTP {response.status_code}): {response.text}")
        return response.json()

    @staticmethod
    def get_stream() -> any:
        response = requests.get(
            "https://api.twitter.com/2/tweets/search/stream", headers=TwitterApi._create_headers(), stream=True,
        )
        if response.status_code != 200:
            raise Exception(f"Cannot get stream (HTTP {response.status_code}): {response.text}")

        return response
