"""Bounded hacker_news operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import HackerNewsClient


class Client(BaseClient):
    provider = "hacker_news"
    implementation = HackerNewsClient
    origins = ("https://hacker-news.firebaseio.com",)
    operations = (
        "get_top_stories",
        "get_new_stories",
        "get_best_stories",
        "get_ask_stories",
        "get_show_stories",
        "get_job_stories",
        "get_item",
        "get_user",
        "get_items_batch",
    )
