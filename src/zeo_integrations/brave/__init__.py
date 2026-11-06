"""Bounded brave operations; credentials injected by Connect."""

from zeo_integrations._http import Client as BaseClient

from ._ported import BraveClient


class Client(BaseClient):
    provider = "brave"
    implementation = BraveClient
    origins = ("https://api.search.brave.com",)
    operations = ("web_search", "image_search", "video_search", "news_search")
