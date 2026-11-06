from zeo_integrations._http import Client as BaseClient

from ._ported import TwitterClient


class Client(BaseClient):
    provider = "x"
    implementation = TwitterClient
    origins = ("https://twitter-api45.p.rapidapi.com",)
    operations = (
        "get_user_profile",
        "get_me",
        "get_user_timeline",
        "get_user_following",
        "get_user_followers",
        "get_tweet",
        "get_tweet_retweets",
        "search_tweets",
        "get_tweet_thread",
        "get_latest_replies",
        "get_list_timeline",
        "get_community_timeline",
        "get_list_followers",
        "get_list_members",
        "get_space",
    )
